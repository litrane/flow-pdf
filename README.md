# flow-pdf

flow-pdf converts PDFs into fluid and dynamic HTML documents, transforming the static layout of PDFs into a responsive and user-friendly format.

`pnpm run start`


pip install layoutparser torchvision && pip install "git+https://github.com/facebookresearch/detectron2.git@v0.5#egg=detectron2"

poetry add layoutparser torchvision
poetry add "git+https://github.com/facebookresearch/detectron2.git@v0.5#egg=detectron2"


poetry add git+https://github.com/karantan/ansible.git@v2.6.0.1

poetry add git+https://github.com/facebookresearch/detectron2.git@v0.5

pip install "detectron2@git+https://github.com/facebookresearch/detectron2.git@v0.5#egg=detectron2"

git clone https://github.com/facebookresearch/detectron2.git
cd detectron2
git checkout -q 82a57ce0b70057685962b352535147d9a8118578
cd ..
python -m pip install -e detectron2

torch = "1.10.0+cpu"


pip install torch==1.10.0+cpu torchvision==0.11.0+cpu torchaudio==0.10.0 -f https://download.pytorch.org/whl/torch_stable.html
python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html

```sh
cat>/etc/pacman.d/mirrorlist<<EOF
Server = https://mirrors.ustc.edu.cn/archlinux/\$repo/os/\$arch
EOF

pacman -Syu --noconfirm
pacman -S miniconda --noconfirm

source /opt/miniconda/etc/profile.d/conda.sh

 https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/

# conda create -n py310 python=3.10
# conda activate py310

conda create -n py39 python=3.9

pip install torch==1.10.0+cpu torchvision==0.11.0+cpu torchaudio==0.10.0 -f https://download.pytorch.org/whl/torch_stable.html
python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch1.10/index.html
pip install pymupdf pyyaml htutil scikit-learn layoutparser fastapi "uvicorn[standard]" python-multipart pymupdf

pacman -S opencv

cd layout-parser-be
uvicorn main:app --reload --host 0.0.0.0

ln -s /tmp/flow-pdf/out ./data/out

```
