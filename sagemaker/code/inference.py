from transformers import AutoTokenizer, AutoModel
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#CLS Pooling - Take output from first token
def cls_pooling(model_output):
    return model_output.last_hidden_state[:, 0]

def model_fn(model_dir):
    # Load model from HuggingFace Hub
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModel.from_pretrained(model_dir)
    model.eval()  # only inference

    return model.to(device), tokenizer

def predict_fn(data, model_and_tokenizer):
    """
    Args:
        data (dict): dict of request JSON with sentence in "inputs"
        NOTE we predict embeddings only for the first sentence
    """

    model, tokenizer = model_and_tokenizer
    
    # Tokenize sentences
    sentence = data.pop("inputs", data)[0]
    encoded_input = tokenizer(sentence, padding=True,
                              truncation=True, return_tensors='pt').to(device)

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input, return_dict=True)

    # Perform pooling
    embedding = cls_pooling(model_output)

    return {"embedding": embedding[0].cpu().tolist()}
