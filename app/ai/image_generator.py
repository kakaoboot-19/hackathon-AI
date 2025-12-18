# image_generator.py
import torch
from diffusers import FluxPipeline

def generate_image(prompt: str, model_name: str, output_path: str):
    pipe = FluxPipeline.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16
    )
    pipe.enable_model_cpu_offload()

    image = pipe(
        prompt,
        guidance_scale=0.0,
        num_inference_steps=4,
        max_sequence_length=256,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]

    image.save(output_path)
