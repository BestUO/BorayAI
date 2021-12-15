import torch
from HuggingFace.transformers import MarianTokenizer, MarianMTModel

def validmarianmtmodel():
    # src = 'fr'  # source language
    # trg = 'en'  # target language
    # sample_text = ["où est l'arrêt de bus ?"]
    # model_name = f'Helsinki-NLP/opus-mt-{src}-{trg}'
    # model_name = "/home/uncleorange/myssd/translate/Helsinki-NLP/opus-mt-fr-en"

    src = 'zh'  # source language
    trg = 'en'  # target language
    sample_text = ["连续的失败已经让我精疲力尽","我要崩溃了","从入门到放弃"]
    model_name = f'Helsinki-NLP/opus-mt-{src}-{trg}'
    model_name = "/home/uncleorange/myssd/translate/Helsinki-NLP/opus-mt-zh-en"

    model = MarianMTModel.from_pretrained(model_name).to("cuda")
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    batch = tokenizer(sample_text, return_tensors="pt", padding=True).to("cuda")
    gen = model.generate(**batch)
    print(tokenizer.batch_decode(gen, skip_special_tokens=True))

def GetModel(usegpu, config):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    model = MarianMTModel.from_pretrained(config["zh_en"]).to(device)
    tokenizer = MarianTokenizer.from_pretrained(config["zh_en"])
    
    return model, tokenizer


def Eval(usegpu, model, batch):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    model, tokenizer = model

    response  = []
    for texts in batch:
        result = tokenizer(texts, return_tensors="pt", padding=True).to(device)
        gen = model.generate(**result)
        response += tokenizer.batch_decode(gen, skip_special_tokens=True)
    return "/".join(response)

if __name__ == "__main__":
    validmarianmtmodel()
