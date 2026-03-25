# MIT License
#
# Copyright (c) 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY
#
# This file serves as the Dockerfile code that is used to build the container image for
# building splats using NerfStudio, GSplat, Colmap, etc

# nosemgrep: dockerfile-source-not-pinned
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-devel

# Only build for supported GPU architectures
#P3=7.0, G4dn=7.5, P4d=8.0, g5=8.6, g6/g6e=8.9
ENV TORCH_CUDA_ARCH_LIST="7.0 7.5 8.0 8.6 8.9"
ENV TCNN_CUDA_ARCHITECTURES=70;75;80;86;89
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/lib
ENV PATH=/usr/local/cuda-11.8/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:${LD_LIBRARY_PATH}

# Ensures that Python outputs everything that's printed directly to the terminal (so logs can be seen in real-time)
ENV PYTHONUNBUFFERED=TRUE

# Ensures Python doesn't try to write .pyc files to disk (useful for improving performance in some scenarios)
ENV PYTHONDONTWRITEBYTECODE=TRUE

# Create code path ENV VAR for container
ARG CODE_PATH
ENV CODE_PATH="/opt/ml/code"

# Create model path ENV VAR for container
ARG MODEL_PATH
#ENV MODEL_PATH="/opt/ml/model"
ENV MODEL_PATH="/opt/ml/input/data/model"

# Create build argument for container
ARG DATASET_PATH
ENV DATASET_PATH="/opt/ml/input/data/train"

ARG LOCAL_DEBUG
ENV LOCAL_DEBUG=${LOCAL_DEBUG}

ARG UUID
ENV UUID=${UUID}

ARG S3_INPUT
ENV S3_INPUT=${S3_INPUT}

ARG S3_OUTPUT
ENV S3_OUTPUT=${S3_OUTPUT}

ARG FILENAME
ENV FILENAME=${FILENAME}

ENV PATH="/usr/local/bin:${PATH}"

FROM base AS builder

# Prepare the container environment and directories
RUN mkdir -p ${CODE_PATH}
WORKDIR ${CODE_PATH}

# Install build/runtime dependencies needed during builds
RUN truncate -s0 /tmp/preseed.cfg && \
    (echo "tzdata tzdata/Areas select America" >> /tmp/preseed.cfg) && \
    (echo "tzdata tzdata/Zones/America select Los_Angeles" >> /tmp/preseed.cfg) && \
    debconf-set-selections /tmp/preseed.cfg && \
    rm -f /etc/timezone /etc/localtime && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true \
    apt-get install -y tzdata

RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN apt-get update -y
RUN apt-get install wget -y

RUN DEBIAN_FRONTEND=noninteractive apt-get clean && apt-get update -y && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    git \
    unzip \
    make \
    ninja-build \
    build-essential \
    libboost-program-options-dev \
    libboost-filesystem-dev \
    libboost-graph-dev \
    libboost-system-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgtest-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libceres-dev \
    libffi-dev \
    libgflags-dev \
    libatlas-base-dev \
    libsuitesparse-dev \
    gcc-10 g++-10 \
    libssl-dev \
    libbz2-dev \
    libexpat1-dev \
    zlib1g-dev \
    liblzma-dev \
    libreadline-dev \
    libncursesw5-dev \
    libdb-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN cd /usr/src \
    && wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz \
    && tar -xzf Python-3.11.0.tgz \
    && cd Python-3.11.0 \
    && ./configure --enable-optimizations --with-openssl=/usr --prefix=/usr/local --with-system-ffi --with-system-expat --enable-loadable-sqlite-extensions \
    && make -j $(nproc) \
    && make altinstall \
    && cd /usr/src && rm -rf Python-3.11.0*

RUN ln -sf /usr/local/bin/python3.11 /usr/local/bin/python \
    && ln -sf /usr/local/bin/pip3.11 /usr/local/bin/pip \
    && ln -sf /usr/local/bin/pip3 /usr/local/bin/pip

ENV PATH=/usr/local/bin:${PATH}
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages:/usr/local/lib/python3.11/dist-packages:${CODE_PATH}

RUN pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
RUN pip install "setuptools<70.0.0" ninja boto3 packaging rich natsort trimesh onnxruntime onnxruntime-gpu
RUN pip install --no-cache-dir scipy 'numpy<2.0.0' Pillow>=10.3.0 timm einops omegaconf fvcore iopath
RUN pip install git+https://github.com/NVlabs/tiny-cuda-nn.git#subdirectory=bindings/torch

RUN wget https://github.com/Kitware/CMake/releases/download/v3.30.3/cmake-3.30.3-linux-x86_64.sh \
    && mkdir /opt/cmake \
    && sh cmake-3.30.3-linux-x86_64.sh --prefix=/opt/cmake --skip-license \
    && ln -s /opt/cmake/bin/cmake /usr/local/bin/cmake \
    && rm cmake-3.30.3-linux-x86_64.sh

RUN git clone --single-branch --depth=1 --branch "3.4" https://gitlab.com/libeigen/eigen.git
RUN mkdir -p ${CODE_PATH}/eigen/build
WORKDIR ${CODE_PATH}/eigen/build
RUN cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="/usr/local/bin/eigen/3.4"
RUN make install
ENV CMAKE_PREFIX_PATH="/usr/local/bin/eigen/3.4"
ENV Eigen3_DIR="/usr/local/bin/eigen/3.4"
WORKDIR ${CODE_PATH}

RUN wget https://github.com/ceres-solver/ceres-solver/archive/refs/tags/2.0.0.tar.gz
RUN tar -xvzf 2.0.0.tar.gz && rm 2.0.0.tar.gz && mkdir ceres-bin && cd ceres-bin && \
    cmake -DEXPORT_BUILD_DIR=ON ../ceres-solver-2.0.0 && make -j3 && make install
ENV Ceres_DIR=${CODE_PATH}/ceres-bin
WORKDIR ${CODE_PATH}

RUN git clone https://github.com/colmap/colmap.git \
    && cd colmap \
    && mkdir build && cd build \
    && cmake .. -GNinja -DCMAKE_CUDA_ARCHITECTURES='${TCNN_CUDA_ARCHITECTURES}' -DMARCH_NATIVE=OFF \
    && ninja install

# ... build the rest of your tooling here ...

FROM base AS runtime

RUN mkdir -p ${CODE_PATH}
WORKDIR ${CODE_PATH}

# Copy only what you need from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder ${CODE_PATH} ${CODE_PATH}

# Copy application files last
RUN mkdir -p ${CODE_PATH}/video_processing \
    && mkdir -p ${CODE_PATH}/image_processing \
    && mkdir -p ${CODE_PATH}/sfm \
    && mkdir -p ${CODE_PATH}/training \
    && mkdir -p ${CODE_PATH}/spherical \
    && mkdir -p ${CODE_PATH}/segmentation \
    && mkdir -p ${CODE_PATH}/post_processing

COPY ./src/main.py                                              ${CODE_PATH}
COPY ./src/config.json                                          ${CODE_PATH}
COPY ./src/pipeline/pipeline.py                                 ${CODE_PATH}
COPY ./src/pipeline/image_processing/filter_blurry_images.py    ${CODE_PATH}/image_processing
COPY ./src/pipeline/video_processing/simple_video_to_images.py  ${CODE_PATH}/video_processing
COPY ./src/pipeline/sfm/extract_poses_imgs.py                   ${CODE_PATH}/sfm
COPY ./src/pipeline/sfm/process_pose_transforms.py              ${CODE_PATH}/sfm
COPY ./src/pipeline/sfm/update_camera_model.py                  ${CODE_PATH}/sfm
COPY ./src/pipeline/training/colmap_to_nerfstudio_cam.py        ${CODE_PATH}/training
COPY ./src/pipeline/spherical/equirectangular_to_perspective.py ${CODE_PATH}/spherical
COPY ./src/pipeline/spherical/Equirec2Cube.py                   ${CODE_PATH}/spherical
COPY ./src/pipeline/spherical/360ImageConverterforColmap.py     ${CODE_PATH}/spherical
COPY ./src/pipeline/spherical/py360convert.py                   ${CODE_PATH}/spherical
COPY ./src/pipeline/segmentation/remove_object_using_mask.py    ${CODE_PATH}/segmentation
COPY ./src/pipeline/segmentation/remove_background.py           ${CODE_PATH}/segmentation
COPY ./src/pipeline/post_processing/rotate_splat.py             ${CODE_PATH}/post_processing
COPY ./src/pipeline/post_processing/mirror_splat.py             ${CODE_PATH}/post_processing
COPY ./src/pipeline/post_processing/gsplat_pt_to_ply.py         ${CODE_PATH}/post_processing
COPY ./src/pipeline/post_processing/spz                         ${CODE_PATH}/post_processing/spz
COPY ./src/pipeline/segmentation/remove_background_sam2.py      ${CODE_PATH}/sam

WORKDIR ${CODE_PATH}

# ... existing code ...