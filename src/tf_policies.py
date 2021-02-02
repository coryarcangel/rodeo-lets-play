import numpy as np

from tf_agents.policies import py_policy, random_py_policy
from tf_agents.trajectories import policy_step

from kim_logs import get_kim_logger
from heuristic_selector import HeuristicActionSelector


class TfAgentHeuristicPolicy(py_policy.PyPolicy):
    def __init__(self, env):
        self.env = env
        self.selector = HeuristicActionSelector()

        policy_state_spec = ()
        super(TfAgentHeuristicPolicy, self).__init__(
            time_step_spec=env.time_step_spec(),
            action_spec=env.action_spec(),
            policy_state_spec=policy_state_spec)

    def ingest_cur_state(self):
        ai_state = self.env.get_cur_ai_state()
        self.selector.ingest_state(ai_state)

    def _action(self, time_step, policy_state):
        # NOTE: I don't actually use the time_step because I can't yet reverse
        # transform observation to AIState... I grab cur state from env...
        self.ingest_cur_state()

        ai_state = self.env.get_cur_ai_state()
        ai_action_tup = self.selector.select_state_action(ai_state)
        tf_action = self.env.ai_action_to_tf_action(ai_action_tup)
        if self.env.action_spec_mode == 1:
            tf_action = np.array([tf_action])

        # NOTE: should I pass info here? probably not necessary?
        info = ()
        return policy_step.PolicyStep(tf_action, policy_state, info)

    def get_status(self, env, tf_action):
        ai_state = env.get_cur_ai_state()
        return self.selector.get_state_status(ai_state)


class TfAgentBlendedPolicy(py_policy.PyPolicy):
    def __init__(self, env, deep_q_manager, deep_q_weighted_policy, other_weighted_policies):
        """ Basically pretend to be a deep q policy, but use actions
        from other policies random-Probabalisticly """
        self.env = env
        self.deep_q_manager = deep_q_manager
        self.logger = get_kim_logger('TfAgentBlendedPolicy')

        policies = [wp[0] for wp in other_weighted_policies]
        dqp = self.deep_q_policy = deep_q_weighted_policy[0]
        self.policies = [dqp] + policies

        dqpw = deep_q_weighted_policy[1]
        weights = [dqpw] + [wp[1] for wp in other_weighted_policies]
        total_weight = float(sum(weights))
        self.policy_probs = [w / total_weight for w in weights]

        names = self.policy_names = ['DEEP_Q'] + [p[2] for p in other_weighted_policies]

        weights_str = ' - '.join([names[i] + ': ' + str(weights[i]) for i in range(len(weights))])
        self.logger.info('Policy weights: {}'.format(weights_str))

        h_pols = [p[0] for p in other_weighted_policies if p[2] == 'Heuristic']
        self.heuristic_policy = h_pols[0] if len(h_pols) > 0 else None

        self.most_recent_policy_choice = None

        super(TfAgentBlendedPolicy, self).__init__(
            time_step_spec=env.time_step_spec(),
            action_spec=env.action_spec(),
            policy_state_spec=deep_q_manager.agent.policy.policy_state_spec,
            info_spec=deep_q_manager.agent.policy.info_spec)

    def _get_initial_state(self, batch_size=None):
        return self.deep_q_policy.get_initial_state(batch_size)

    def _action(self, time_step, policy_state):
        # Choose policy for this action
        probs = self.policy_probs
        policy_idx = np.random.choice(len(self.policies), p=probs)
        policy_name = self.policy_names[policy_idx]
        self.logger.info('Chose {} policy'.format(policy_name))
        self.most_recent_policy_choice = policy_name

        # If we didn't choose heuristic policy, allow selector to ingest state
        if policy_name != 'Heuristic' and self.heuristic_policy is not None:
            self.heuristic_policy.ingest_cur_state()

        # Get what the deep q would have done always, to pass state / info
        dq_step = self.deep_q_policy.action(time_step, policy_state)
        if policy_idx == 0:  # first policy is deep q
            return dq_step

        # Get non-deep-q action
        policy = self.policies[policy_idx]
        step = policy.action(time_step, policy_state)

        return policy_step.PolicyStep(step.action, dq_step.state, dq_step.info)

    def get_status(self, env, tf_action):
        status = {
            'reward': env.most_recent_reward,
            'step_num': env.step_num,
            'total_step_num': env.total_step_num,
            'recent_action_step_nums': env.reward_calculator.get_recent_action_step_nums()
        }

        if self.heuristic_policy:
            status.update(self.heuristic_policy.get_status(env, tf_action))

        if self.most_recent_policy_choice is not None:
            status['policy_choice'] = self.most_recent_policy_choice

        return status


class TfAgentPolicyFactory(object):
    def __init__(self, env):
        self.env = env

    # https://www.tensorflow.org/agents/api_docs/python/tf_agents/policies/random_py_policy/RandomPyPolicy
    def get_random_policy(self):
        return random_py_policy.RandomPyPolicy(
            self.env.time_step_spec(), self.env.action_spec())

    # https://www.tensorflow.org/agents/api_docs/python/tf_agents/policies/py_policy/PyPolicy
    def get_heuristic_policy(self):
        return TfAgentHeuristicPolicy(self.env)

    # https://www.tensorflow.org/agents/api_docs/python/tf_agents/policies/q_policy/QPolicy
    def get_deep_q_policy(self, deep_q_manager):
        return deep_q_manager.agent.policy

    def get_blended_policy(self,
                           deep_q_manager,
                           deep_q_policy,
                           deep_q_weight=0.5,
                           heuristic_weight=0.4,
                           random_weight=0.1):
        dq_policy = (deep_q_policy, deep_q_weight)

        other_policies = [p for p in [
            (self.get_heuristic_policy(), heuristic_weight, 'Heuristic'),
            (self.get_random_policy(), random_weight, 'Random')
        ] if p[1] > 0]

        return TfAgentBlendedPolicy(self.env, deep_q_manager, dq_policy, other_policies)
