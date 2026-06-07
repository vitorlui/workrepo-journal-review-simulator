# Lightweight Residual Spatiotemporal Networks for Real-Time Face Anti-Spoofing

## Abstract

We present a lightweight residual spatiotemporal neural network for real-time face anti-spoofing (FAS) and presentation attack detection (PAD). The method targets the computational cost vs accuracy trade-off for deployment on edge computing devices. We evaluate cross-dataset generalization using APCER, BPCER and ACER metrics and report a writer-independent style protocol for unseen attacks. This is a sample manuscript used to exercise the journal-review-simulator pipeline.

Keywords: face anti-spoofing, presentation attack detection, spatiotemporal neural networks, real-time, edge computing

## Introduction

Presentation attack detection is critical for biometric security in video-based identity verification. Replay attacks and print attacks remain challenging under cross-dataset evaluation. We motivate a lightweight FAS model that runs in real time while preserving robustness to unknown attacks.

## Methodology

The proposed approach is a residual spatiotemporal 3D convolutional neural network. We describe the architecture, the training protocol, hyperparameters and seeds. The system design targets low latency and low memory for cloud and edge deployment.

## Experiments

We evaluate on standard FAS datasets using a cross-dataset protocol. Baselines include several spatiotemporal networks. We report APCER, BPCER, ACER, AUC and EER, and measure computational cost.

## Results

The model achieves competitive accuracy with reduced parameters. Cross-dataset generalization is reported with confidence intervals over multiple seeds.

## Limitations

The evaluation is limited to a subset of public datasets. Generalization to fully unknown attack families is not guaranteed.

## References

1. Placeholder reference for the sample manuscript (not a real citation).
