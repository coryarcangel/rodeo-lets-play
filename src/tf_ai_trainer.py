import os
import signal
import sys
import traceback

from tf_ai_env import create_tf_ai_env
from tf_deep_q import TfAgentDeepQManager


def run_and_train_deep_q_policy(num_iterations=100,
                                save_dir='test_deep_q',
                                load_from_checkpoint=True,
                                collect_steps_per_iteration=100):
    env = create_tf_ai_env()

    deep_q_manager = TfAgentDeepQManager(env, {
        'save_dir': save_dir,
        'collect_steps_per_iteration': collect_steps_per_iteration
    })

    if load_from_checkpoint:
        deep_q_manager.restore_checkpoint()

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
