# main.py
from config import (
    JSON_PATH,
    LLM_MODEL,
    IMAGE_MODEL,
    IMAGE_PROMPT_SUFFIX
)
from data_loader import load_github_json
from github_analyzer import analyze_repository
from llm_evaluator import evaluate_project
from image_generator import generate_image

def main():
    data = load_github_json(JSON_PATH)

    analysis = analyze_repository(data)

    evaluation = evaluate_project(analysis, LLM_MODEL)

    final_result = evaluation["final_result"]
    print("최종 평가:", final_result)

    image_prompt = f"{final_result}, {IMAGE_PROMPT_SUFFIX}"
    generate_image(image_prompt, IMAGE_MODEL, "demo_test_image.png")

if __name__ == "__main__":
    main()
