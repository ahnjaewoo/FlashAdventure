import datetime
import json
import logging
import os
import time

logger = logging.getLogger("desktopenv.experiment")

def run_single_example(agent, env, example, max_steps, instruction, args, example_result_dir, scores):
    runtime_logger = setup_logger(example, example_result_dir)
    agent.reset(runtime_logger)
    env.reset(task_config=example)
    time.sleep(3)  # Shorter wait for local environment
    obs = env._get_obs()
    done = False
    step_idx = 0

    while not done and step_idx < max_steps:
        response, actions = agent.predict(instruction, obs)

        for action in actions:
            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
            logger.info("Step %d: %s", step_idx + 1, action)

            obs, reward, done, info = env.step(action, args.sleep_after_execution)

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)

            # Save screenshot
            screenshot_filename = f"step_{step_idx + 1}_{action_timestamp}.png"
            screenshot_path = os.path.join(example_result_dir, screenshot_filename)
            if hasattr(obs['screenshot'], "save"):
                obs['screenshot'].save(screenshot_path)
            else:
                logger.warning("Screenshot object has no .save() method — skipping save.")

            # Log trajectory
            traj_path = os.path.join(example_result_dir, "traj.jsonl")
            with open(traj_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "step_num": step_idx + 1,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "screenshot_file": screenshot_filename
                }) + "\n")

            if done:
                logger.info("The episode is done.")
                break

        step_idx += 1

    # Dummy evaluation for local
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    scores.append(result)

    result_path = os.path.join(example_result_dir, "result.txt")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(f"{result}\n")


def setup_logger(example, example_result_dir):
    runtime_logger = logging.getLogger(f"desktopenv.example.{example['id']}")
    runtime_logger.setLevel(logging.DEBUG)
    log_file = os.path.join(example_result_dir, "runtime.log")
    runtime_logger.addHandler(logging.FileHandler(log_file))
    return runtime_logger