# Settings and Hardware that have been "tested"

This is the hardware on which I have been "developing" this whole mess, and should serve as some sort of a baseline. 

 **YMMV**

## Hardware & Software
LM Studio 0.3.17, build 11
 - https://lmstudio.ai/
Windows 11
13th Gen Intel(R) Core(TM) i7-13620H 
16 gig onboard ram, gefore rtx 4060 laptop gpu w/ 8gig VRAM

## Model
Model: `qwen2.5-coldbrew-aetheria-test2_tools`
  - https://huggingface.co/Theros/Qwen2.5-ColdBrew-Aetheria-test2_tools-Q5_K_M-GGUF
  - I've yet to find a compatible model for speculative decoding
  - must be trained to use tools in order for mcp to work, otherwise model has no idea what you're talking about
## Settings: (I have no idea what I'm doing) 
- Temperature at 0.1 (out of 1.0)
  - Trying to keep this low to reduce the variance in code quality
- Context: `16,372` / `131,072`
  - The model supports up to `131,072`, going anywhere near that quickly overloads the GPU.
- Steadily increasing my context window size, so long as the responses are stable.
  - Set incorrectly and they tend to babble endlessly
