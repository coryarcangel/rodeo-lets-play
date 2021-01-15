import os
import signal
import sys
import traceback

from tf_agents.environments import tf_py_environment

from config import configure_logging
from device_client import DeviceClient
from tf_ai_env import DeviceClientTfEnv
from tf_deep_q import load_saved_policy
from tf_policies import TfAgentPolicyFactory


def create_client_env():
    configure_logging()

    device_client = DeviceClient()
    device_client.start()

    env = DeviceClientTfEnv(device_client)

    return env


def run_ai_with_policy(env, policy):
    tf_env = tf_py_environment.TFPyEnvironment(env)

    while True:
        time_step = tf_env.reset()
        while not time_step.is_last():
            action_step = policy.action(time_step)
            time_step = tf_env.step(action_step.action)


def run_ai_with_random_policy():
    env = create_client_env()

    factory = TfAgentPolicyFactory(env)
    policy = factory.get_random_policy()

    run_ai_with_policy(env, policy)


def run_ai_with_saved_blended_policy(name='policy',
                                     dir=os.getcwd() + '/deep_q_save',
                                     deep_q_weight=0.5,
                                     heuristic_weight=0.4,
                                     random_weight=0.1):
    env = create_client_env()

    # Load Deep Q Policy
    policy_dir = os.path.join(dir, name)
    deep_q_policy = load_saved_policy(policy_dir)

    # Create Blended Policy
    factory = TfAgentPolicyFactory(env)
    blended_policy = factory.get_blended_policy(deep_q_policy,
                                                deep_q_weight=deep_q_weight,
                                                heuristic_weight=heuristic_weight,
                                                random_weight=random_weight)

    run_ai_with_policy(env, blended_policy)


if __name__ == '__main__':
    try:
        run_ai_with_random_policy()
        # run_ai_with_saved_blended_policy()
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    sys.exit(0)
