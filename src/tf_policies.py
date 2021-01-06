import numpy as np

from tf_agents.policies import py_policy, random_py_policy
from tf_agents.trajectories import policy_step

from ai_heuristic import HeuristicActionSelector


class TfAgentHeuristicPolicy(py_policy.PyPolicy):
    def __init__(self, env):
        self.env = env
        self.selector = HeuristicActionSelector()

        policy_state_spec = ()
        super(TfAgentHeuristicPolicy, self).__init__(
            time_step_spec=env.time_step_spec(),
            action_spec=env.action_spec(),
            policy_state_spec=policy_state_spec)

    def _action(self, time_step, policy_state):
        # NOTE: I don't actually use the time_step because I can't yet reverse
        # transform observation to AIState... I grab cur state from env...
        ai_state = self.env.get_cur_ai_state()
        ai_action_tup = self.selector.select_state_action(ai_state)
        tf_action = self.env.ai_action_to_tf_action(ai_action_tup)

        # NOTE: should I pass info here? probably not necessary?
        info = ()
        return policy_step.PolicyStep(tf_action, policy_state, info)


class TfAgentBlendedPolicy(py_policy.PyPolicy):
    def __init__(self, env, deep_q_weighted_policy, other_weighted_policies):
        """ Basically pretend to be a deep q policy, but use actions
        from other policies random-Probabalisticly """
        self.env = env

        policies = [wp[0] for wp in other_weighted_policies]
        dqp = self.deep_q_policy = deep_q_weighted_policy[0]
        self.policies = [dqp] + policies

        dqpw = deep_q_weighted_policy[0]
        weights = [dqpw] + [wp[1] for wp in other_weighted_policies]
        total_weight = float(sum(weights))
        self.policy_probs = [w / total_weight for w in weights]

        super(TfAgentBlendedPolicy, self).__init__(
            time_step_spec=env.time_step_spec(),
            action_spec=env.action_spec(),
            policy_state_spec=dqp.policy_state_spec(),
            info_spec=dqp.info_spec())

    def get_initial_state(self, batch_size=None):
        return self.deep_q_policy.get_initial_state(batch_size)

    def _action(self, time_step, policy_state):
        probs = self.policy_probs
        policy_idx = np.random.choice(len(self.policies), p=probs)

        dq_step = self.deep_q_policy.action(time_step, policy_state)
        if policy_idx == 0:  # first policy is deep q
            return dq_step

        policy = self.policies[policy_idx]
        step = policy.action(time_step, policy_state)

        return policy_step.PolicyStep(step.action, dq_step.state, dq_step.info)


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
    def get_deep_q_policy(self, deep_q_agent):
        return deep_q_agent.policy

    def get_blended_policy(self,
                           deep_q_policy,
                           deep_q_weight=0.5,
                           heuristic_weight=0.4,
                           random_weight=0.1):
        dq_policy = (deep_q_policy, deep_q_weight)

        other_policies = [p for p in [
            (self.get_heuristic_policy(), heuristic_weight),
            (self.get_random_policy(), random_weight)
        ] if p[1] > 0]

        return TfAgentBlendedPolicy(self.env, dq_policy, other_policies)
