import torch
import numpy as np
from pathlib import Path
import yaml
from string import punctuation
from g2p_en import G2p
from pypinyin import pinyin, Style
import re
from TextToSpeech.text import text_to_sequence
from TextToSpeech.utils.tools import to_device, synth_samples_new
from TextToSpeech.utils.model import get_model_new, get_vocoder_new

mean = np.array([0.485, 0.456, 0.406])


def GetModel(usegpu, args):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    models = {}
    for modelname in args:
        configs, lexicon = PrepareBaseInfo(modelname)
        enfastspeech = get_model_new(configs, device, args[modelname][0])
        vocoder = get_vocoder_new(device, Path(__file__).parent.joinpath("hifigan","config.json"), args[modelname][1])
        g2p = G2p()
        models[modelname] = [enfastspeech, vocoder, configs, lexicon, g2p]
    return models

def Eval(usegpu, model, param):
    device = torch.device("cuda" if usegpu and torch.cuda.is_available() else "cpu")
    with torch.no_grad():
        text, modelpath, speakerid, modelname, resultpath = param
        fastspeech, vocoder, configs, lexicon, g2p = model[modelname]
        batchs, control_values = PrepareText(modelname, speakerid, text, configs[0], lexicon, g2p)
        synthesize(device, fastspeech, configs, vocoder, batchs, control_values, resultpath)

def PrepareText(modelname, speakerid, text, preprocess_config, lexicon, g2p):
    ids = raw_texts = [text[:100]]
    speakers = np.array([speakerid])
    if modelname == "en":
        texts = np.array([preprocess_english(text, preprocess_config, lexicon, g2p)])
    else :
        texts = np.array([preprocess_mandarin(text, preprocess_config, lexicon)])
    text_lens = np.array([len(texts[0])])
    batchs = [(ids, raw_texts, speakers, texts, text_lens, max(text_lens))]
    control_values = 1.0,1.0,1.0
    return batchs, control_values

def PrepareBaseInfo(modelname):
    if modelname == "en":
        preprocess_config = str(Path(__file__).parent.joinpath("config","LJSpeech","preprocess.yaml"))
        model_config = str(Path(__file__).parent.joinpath("config","LJSpeech","model.yaml"))
        train_config = str(Path(__file__).parent.joinpath("config","LJSpeech","train.yaml"))
    else:
        preprocess_config = str(Path(__file__).parent.joinpath("config","AISHELL3","preprocess.yaml"))
        model_config = str(Path(__file__).parent.joinpath("config","AISHELL3","model.yaml"))
        train_config = str(Path(__file__).parent.joinpath("config","AISHELL3","train.yaml"))

    preprocess_config = yaml.load(open(preprocess_config, "r"), Loader=yaml.FullLoader)
    model_config = yaml.load(open(model_config, "r"), Loader=yaml.FullLoader)
    train_config = yaml.load(open(train_config, "r"), Loader=yaml.FullLoader)
    configs = (preprocess_config, model_config, train_config)
    lexicon = read_lexicon(str(Path(__file__).parent.joinpath(preprocess_config["path"]["lexicon_path"])))
    return configs, lexicon
    

def synthesize(device, model, configs, vocoder, batchs, control_values, outpath):
    preprocess_config, model_config, train_config = configs
    pitch_control, energy_control, duration_control = control_values

    for batch in batchs:
        batch = to_device(batch, device)
        with torch.no_grad():
            # Forward
            output = model(
                *(batch[2:]),
                p_control=pitch_control,
                e_control=energy_control,
                d_control=duration_control
            )
            synth_samples_new(
                batch,
                output,
                vocoder,
                model_config,
                preprocess_config,
                outpath,
            )

def read_lexicon(lex_path):
    lexicon = {}
    with open(lex_path) as f:
        for line in f:
            temp = re.split(r"\s+", line.strip("\n"))
            word = temp[0]
            phones = temp[1:]
            if word.lower() not in lexicon:
                lexicon[word.lower()] = phones
    return lexicon

def preprocess_english(text, preprocess_config, lexicon, g2p):
    text = text.rstrip(punctuation)

    phones = []
    words = re.split(r"([,;.\-\?\!\s+])", text)
    for w in words:
        if w.lower() in lexicon:
            phones += lexicon[w.lower()]
        else:
            phones += list(filter(lambda p: p != " ", g2p(w)))
    phones = "{" + "}{".join(phones) + "}"
    phones = re.sub(r"\{[^\w\s]?\}", "{sp}", phones)
    phones = phones.replace("}{", " ")

    print("Raw Text Sequence: {}".format(text))
    print("Phoneme Sequence: {}".format(phones))
    sequence = np.array(
        text_to_sequence(
            phones, preprocess_config["preprocessing"]["text"]["text_cleaners"]
        )
    )

    return np.array(sequence)

def preprocess_mandarin(text, preprocess_config, lexicon):
    phones = []
    pinyins = [
        p[0]
        for p in pinyin(
            text, style=Style.TONE3, strict=False, neutral_tone_with_five=True
        )
    ]
    for p in pinyins:
        if p in lexicon:
            phones += lexicon[p]
        else:
            phones.append("sp")

    phones = "{" + " ".join(phones) + "}"
    print("Raw Text Sequence: {}".format(text))
    print("Phoneme Sequence: {}".format(phones))
    sequence = np.array(
        text_to_sequence(
            phones, preprocess_config["preprocessing"]["text"]["text_cleaners"]
        )
    )

    return np.array(sequence)