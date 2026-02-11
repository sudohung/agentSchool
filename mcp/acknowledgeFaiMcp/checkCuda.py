import torch

def check_cuda():
    print("PyTorch version:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA version:", torch.version.cuda)
    print("Number of CUDA devices:", torch.cuda.device_count())

    if torch.cuda.is_available():
        print("Current CUDA device:", torch.cuda.current_device())
        print("CUDA device name:", torch.cuda.get_device_name(0))
    else:
        print("CUDA is not available. Please check your NVIDIA drivers and PyTorch installation.")

if __name__ == "__main__":
    check_cuda()