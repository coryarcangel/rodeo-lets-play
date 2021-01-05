
from tf_agents.policies import py_policy, random_py_policy
from tf_agents.trajectories import policy_step

from ai_heuristic import HeuristicActionSelector


class TfAgentHeuristicPolicy(py_policy.PyPolicy):
    def __init__(self, env):
        self.env = env
        self.selector = HeuristicActionSelector()

        super(TfAgentHeuristicPolicy, self).__init__(
            time_step_spec=env.time_step_spec(),
            action_spec=env.action_spec(),
            policy_state_spec=policy_state_spec)

    def _action(self, time_step, policy_state):
        info = ()
        return policy_step.PolicyStep(action, policy_state, info)


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
    def get_deep_q_policy(self):
        pass

    def get_blended_policy(self, weighted_policies):
        pass
