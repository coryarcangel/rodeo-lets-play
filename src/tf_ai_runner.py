import os
import signal
import sys
import traceback

from tf_agents.environments import tf_py_environment

from config import TF_AI_POLICY_WEIGHTS
from tf_ai_env import create_tf_ai_env
from tf_deep_q import load_saved_policy
from tf_policies import TfAgentPolicyFactory


def run_ai_with_policy(env, policy):
    tf_env = tf_py_environment.TFPyEnvironment(env)

    while True:
        time_step = tf_env.reset()
        while not time_step.is_last():
            action_step = policy.action(time_step)
            time_step = tf_env.step(action_step.action)


def run_ai_with_random_policy():
    env = create_tf_ai_env()

    factory = TfAgentPolicyFactory(env)
    policy = factory.get_random_policy()

    run_ai_with_policy(env, policy)


def run_ai_with_heuristic_policy():
    env = create_tf_ai_env()

    factory = TfAgentPolicyFactory(env)
    policy = factory.get_heuristic_policy()

    run_ai_with_policy(env, policy)


def run_ai_with_saved_blended_policy(name='policy',
                                     dir=os.getcwd() + '/deep_q_save',
                                     weights=TF_AI_POLICY_WEIGHTS):
    env = create_tf_ai_env()

    def get_weight(key):
        return weights[key] if key in weights else 0

    # Load Deep Q Policy
    policy_dir = os.path.join(dir, name)
    deep_q_policy = load_saved_policy(policy_dir)

    # Create Blended Policy
    factory = TfAgentPolicyFactory(env)

    blended_policy = factory.get_blended_policy(deep_q_policy,
                                                deep_q_weight=get_weight('deep_q'),
                                                heuristic_weight=get_weight('heuristic'),
                                                random_weight=get_weight('random'))

    run_ai_with_policy(env, blended_policy)


if __name__ == '__main__':
    try:
        # run_ai_with_random_policy()
        run_ai_with_heuristic_policy()
        # run_ai_with_saved_blended_policy()
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    sys.exit(0)
