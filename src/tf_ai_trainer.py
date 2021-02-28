import os
import signal
import sys
import traceback

from config import TF_DEEPQ_POLICY_SAVE_DIR
from device_client import DeviceClient
from tf_ai_env import DeviceClientTfEnv
from tf_deep_q import TfAgentDeepQManager


def run_and_train_deep_q_policy(num_iterations=1000,
                                save_dir=TF_DEEPQ_POLICY_SAVE_DIR,
                                load_from_checkpoint=True,
                                collect_steps_per_iteration=100):
    device_client = DeviceClient(safeguard_menu_clicks=True)
    device_client.start()

    env = DeviceClientTfEnv(device_client)

    deep_q_manager = TfAgentDeepQManager(env, {
        'save_dir': save_dir,
        'collect_steps_per_iteration': collect_steps_per_iteration,
        'checkpoint_save_interval': 20,
        'policy_save_interval': 20,
        'epsilon_greedy': 0.2,
        'assumed_start_steps': 0
    })

    if load_from_checkpoint:
        deep_q_manager.restore_checkpoint()

    # env.reset()
    deep_q_manager.train(num_iterations)
    deep_q_manager.save_checkpoint()
    deep_q_manager.save_policy()

    # have to kill in this crazy way because of like tensorflow threading?
    os.kill(os.getpid(), signal.SIGKILL)


if __name__ == '__main__':
    try:
        run_and_train_deep_q_policy()
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    sys.exit(0)
