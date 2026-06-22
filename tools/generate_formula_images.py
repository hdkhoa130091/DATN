from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "presentation" / "canva_ai_package" / "formula_images"


FORMULAS = [
    (
        "policy_ratio",
        r"$r_t(\theta)=\frac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_{\mathrm{old}}}(a_t \mid s_t)}$",
        "Policy ratio",
    ),
    (
        "ppo_clip",
        r"$L^{CLIP}(\theta)=\mathbb{E}_t\left[\min\left(r_t(\theta)\hat{A}_t,\ \mathrm{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\hat{A}_t\right)\right]$",
        "PPO clipped objective",
    ),
    (
        "value_loss",
        r"$L^{VF}(\theta)=\mathbb{E}_t\left[\left(V_\theta(s_t)-R_t\right)^2\right]$",
        "Value loss",
    ),
    (
        "entropy_bonus",
        r"$L^{ENT}(\theta)=\mathbb{E}_t\left[H(\pi_\theta(\cdot \mid s_t))\right]$",
        "Entropy bonus",
    ),
    (
        "total_objective",
        r"$L(\theta)=L^{CLIP}(\theta)-c_1L^{VF}(\theta)+c_2L^{ENT}(\theta)$",
        "Tong objective",
    ),
    (
        "td_error",
        r"$\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)$",
        "TD error",
    ),
    (
        "gae_advantage",
        r"$\hat{A}_t=\delta_t+(\gamma\lambda)\delta_{t+1}+(\gamma\lambda)^2\delta_{t+2}+\cdots$",
        "GAE advantage",
    ),
    (
        "returns",
        r"$R_t\approx \hat{A}_t+V(s_t)$",
        "Bootstrapped return",
    ),
]


def render_formula(filename: str, formula: str, title: str) -> Path:
    fig = plt.figure(figsize=(12, 2.2), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.text(0.03, 0.70, title, fontsize=20, weight="bold", color="#1F2430", family="DejaVu Sans")
    ax.text(0.03, 0.25, formula, fontsize=24, color="#111111")
    output = OUT_DIR / f"{filename}.png"
    fig.savefig(output, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    return output


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for filename, formula, title in FORMULAS:
        generated.append(render_formula(filename, formula, title))

    index = ROOT / "presentation" / "canva_ai_package" / "cong_thuc_rendered_guide.md"
    lines = [
        "# Công thức đã render thành ảnh\n",
        "\n",
        "Các ảnh dưới đây đã được render đúng định dạng toán và có thể upload thẳng lên Canva:\n",
        "\n",
    ]
    for path in generated:
        lines.append(f"- `formula_images/{path.name}`\n")
    lines.append("\n")
    lines.append("Khuyên dùng: upload cả thư mục `formula_images/` cùng với prompt và markdown để Canva nhìn ra công thức toán rõ hơn.\n")
    index.write_text("".join(lines))
    print(index)


if __name__ == "__main__":
    main()
