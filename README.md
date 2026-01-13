# Reference Graph Builder

### Group 11
- Julian J. Kravanja
- Monika Windhager
- Konrad Zalar

## Description

In this project we try to answer the following research question:

> Can a weighted citation graph - which is constructed by analyzing if and how an argument is argued or critically engaged with - provide meaningful information about how well scientific claims are supported, and help identify citation weaknesses?

We analyze whether citations with higher system-assigned criticality align
with citation weaknesses identified by human annotators, and whether the resulting graph structure helps identify weakly supported referencing patterns.

## Project Structure & Experimental Setup

![Architecture](/Ressources/ReferenceGraphBuilderStructure.png)\
*Figure 1: Project Structure*

## How to reproduce the Results

### Setup
It is strongly recommended by us to use a virtual environment to run this project.
```bash
python -m venv .venv
.venv\Scripts\Activate
```

Run `requirements.txt`
```bash
pip install -r requirements.txt
```

[Download](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf) the necessary Llama Model (mistral-7b-instruct-v0.2.Q5_K_M) from [Huggingface](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q5_K_M.gguf) and add the `.gguf` file to the [UsageValidator](CiteSide\UsageValidator) folder. 

### Running experiments
From the project root execute the ValidationRunner. 
```bash
python -m CiteSide.Runner.ValidationRunner
```
This will analyze the preconfigured argument and the starting paper for the corresponding dataset. The whole process will take a couple of minutes.

### Configure own experiments

To change the Dataset add the location of your custom dataset to the `loadDataset(Path/to/custom/Dataset)` function in [ValidationRunner](/CiteSide/Runner/ValidationRunner.py#L55). (check [Dataset](#dataset) for the correct format of the data) 

To run the experiment with a custom argument change the `argument = "My custom argument"` parameter in the main function of the [ValidationRunner](/CiteSide/Runner/ValidationRunner.py#L109)

To change the starting paper adapt the `paper_id = "otherID"` parameter in the main function of the [ValidationRunner](/CiteSide/Runner/ValidationRunner.py#L110)

## Dataset

The dataset used for the experiments is a custom dataset that was specifically designed for our proof-of-concept. It contains 12 publicly available scientific papers regarding the topic of COVID-19.
It is located in the [Data\Input](CiteSide\Data\Input) folder.

The papers were downloaded as PDFs, processed with [GROBID](https://github.com/kermitt2/grobid-client-python) and parsed into a `json` file.

The format of the used Dataset is:
```json
    [
      {
      "paper_id": "Unique ID",
      "title": "Title of the Paper",
      "full_text": "Fulltext paper with citations",
      "abstract": "Abstract",
      "year": "2026",
      "authors": "Author A and Author B (concatenated with 'and')",
      "references": [
        "R1",
        "R2"
      ]
      },
      {
        "paper_id": "Unique ID2",
        ....
      }
    ]
```

While a minimal working dataset has to include:

```json
    [
      {
      "paper_id": "PID",
      "full_text": "Fulltext paper with citations",
      "year": "2026",
      "authors": "Author A and Author B",
      "references": []
      }
    ]
```

## Ressources

Models used in this project:

**sentence-transformers/all-mpnet-base-v2** available on Hugging Face: https://huggingface.co/sentence-transformers/all-mpnet-base-v2


**TheBloke/Mistral-7B-Instruct-v0.2-GGUF** version v0.2.Q5_K_M, available on Hugging Face: 
https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF






