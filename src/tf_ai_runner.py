import os
import signal
import sys
import traceback

from tf_agents.environments import tf_py_environment

from config import TF_AI_POLICY_WEIGHTS, TF_DEEPQ_POLICY_SAVE_DIR
from tf_ai_env import create_tf_ai_env
from tf_deep_q import TfAgentDeepQManager
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


def run_ai_with_saved_blended_policy(policy_name='policy',
                                     save_dir=TF_DEEPQ_POLICY_SAVE_DIR,
                                     weights=TF_AI_POLICY_WEIGHTS):
    env = create_tf_ai_env()

    def get_weight(key):
        return weights[key] if key in weights else 0

    # Load Deep Q Policy
    deep_q_manager = TfAgentDeepQManager(env, {'save_dir': save_dir})
    deep_q_policy = deep_q_manager.load_policy(policy_name)

    # Create Blended Policy
    factory = TfAgentPolicyFactory(env)

    blended_policy = factory.get_blended_policy(deep_q_manager,
                                                deep_q_policy,
                                                deep_q_weight=get_weight('deep_q'),
                                                heuristic_weight=get_weight('heuristic'),
                                                random_weight=get_weight('random'))

    run_ai_with_policy(env, blended_policy)


if __name__ == '__main__':
    try:
        run_ai_with_saved_blended_policy()
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    sys.exit(0)
