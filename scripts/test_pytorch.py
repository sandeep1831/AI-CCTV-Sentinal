"""AI-CCTV Sentinel — PyTorch environment verification script."""

import torch


def main() -> None:
    print("=" * 60)
    print("PyTorch Environment Check")
    print("=" * 60)

    print(f"PyTorch version : {torch.__version__}")
    print(f"CUDA available  : {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA version    : {torch.version.cuda}")
        print(f"GPU count       : {torch.cuda.device_count()}")

        for index in range(torch.cuda.device_count()):
            print(f"GPU {index}         : {torch.cuda.get_device_name(index)}")
    else:
        print("Compute device  : CPU")

    tensor = torch.tensor([1.0, 2.0, 3.0])

    print(f"Tensor test     : {tensor}")
    print("PyTorch check   : PASSED")


if __name__ == "__main__":
    main()
