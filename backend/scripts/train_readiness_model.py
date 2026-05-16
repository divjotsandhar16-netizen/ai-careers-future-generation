import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "readiness_model.json"


def make_training_data(rows: int = 700) -> list[tuple[list[float], float]]:
    random.seed(42)
    samples = []
    for _ in range(rows):
        experience = random.uniform(0, 10)
        projects = random.randint(0, 10)
        skill_match = random.uniform(10, 100)
        confidence = random.randint(1, 10)
        noise = random.uniform(-5, 5)
        score = experience * 5.5 + projects * 4 + skill_match * 0.35 + confidence * 3.5 + noise
        samples.append(([experience, projects, skill_match, confidence], max(0, min(score, 100))))
    return samples


def train_linear_model(samples: list[tuple[list[float], float]], epochs: int = 1800, learning_rate: float = 0.00003):
    weights = [0.0, 0.0, 0.0, 0.0]
    bias = 0.0
    for _ in range(epochs):
        grad_weights = [0.0, 0.0, 0.0, 0.0]
        grad_bias = 0.0
        for features, target in samples:
            prediction = bias + sum(weight * feature for weight, feature in zip(weights, features))
            error = prediction - target
            grad_bias += error
            for index, feature in enumerate(features):
                grad_weights[index] += error * feature
        count = len(samples)
        bias -= learning_rate * grad_bias / count
        for index in range(len(weights)):
            weights[index] -= learning_rate * grad_weights[index] / count
    return bias, weights


def mean_absolute_error(samples: list[tuple[list[float], float]], bias: float, weights: list[float]) -> float:
    errors = []
    for features, target in samples:
        prediction = bias + sum(weight * feature for weight, feature in zip(weights, features))
        errors.append(abs(prediction - target))
    return sum(errors) / len(errors)


def main():
    samples = make_training_data()
    split = int(len(samples) * 0.8)
    train_samples = samples[:split]
    test_samples = samples[split:]
    bias, weights = train_linear_model(train_samples)
    model = {
        "bias": bias,
        "weights": {
            "experience_years": weights[0],
            "projects_count": weights[1],
            "skill_match_percent": weights[2],
            "interview_confidence": weights[3],
        },
    }
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(model, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"MAE: {mean_absolute_error(test_samples, bias, weights):.2f}")


if __name__ == "__main__":
    main()
