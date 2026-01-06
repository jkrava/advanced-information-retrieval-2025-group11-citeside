# HerBERT - Reference Graph Builder

## Group 11

## November 2025

## Members

- Dominik Haring — Dataset / Reference Extractor
- Julian J. Kravanja — Dataset / Usage Validator
- Monika Windhager — Reference Extractor / Usage Validator
- Konrad Zalar — Reference Tree Builder / Usage Validator

## Abstract

In this project we work on HerBERT - a system for automatically detecting
weak and / or circular citation practices in scientific writing by constructing a
weighted reference graph from research papers. We plan to combine automated
citation extraction with context-aware assessment of how each referenced source
is used within the citing document. With using a pretrained distilBERT model,
we extract citation relations from full text to reconstruct reference edges, while
a fitted BART model evaluates citation context to assign weights that reflect
argumentative relevance and evidential strength. The then resulting graph al-
lows us to identify claims or topics that rely on poorly supported references or
citation chains that are prone to amplification effects.

With our project we therefore want to offer a proof-of-concept approach for
uncovering “bad practice” referencing patterns and enhancing the transparency
in knowledge distribution and generation in scientific papers.

## Idea (Goal / Research Question)

The goal of this project is to develop a method for extracting citation dependen-
cies from the full text of research papers and constructing a weighted reference
graph in which edge weights represent how critically a cited source contributes
to the citing document’s arguments, methodology, or findings. Using this we
want to detect bad citations and non-proofed claims which have been build on.
Which brings us to our research question:


”Can an automatically constructed, weighted citation graph reveal how well
scientific claims are supported and where citation weaknesses and / or circular
referencing occurs?”

## Visual Depiction

![HerBERT Architecture](/Ressources/HerBERT.png)


*Figure 1: Test and Application Flow*

## Main Task

The Tasks within the work are split into different sub-tasks:

- Reference Extraction: From the plain text of scientific works extracting
    the references to different work and continuing this path building a graph
    of references.
- Usage Validation: Out of the Text (or some snippets, surrounding refer-
    ences and given by the reference extractor) create edge weights for the
    network which tell how critical a work uses some source.
- Graph: A full Graph over the given Database which makes it possible to
    identify topics/contents which are badly cited or not proofed.

## Dataset and Processing

For this project we will have two different type of data sets, the training data
and application data.
As training data, we will be using a data set that includes papers and other
scientific works with already extracted citations as meta data. For one part, it
will be used to train the model to extract the citations out of the application
data and test the resulting model.
Additionally, by applying a simple algorithm, which systematically parses the
citation meta data, we will build a graph – the reference tree – out of the data
set to improve the accuracy of the model. The training data in combination with
the reference tree will also be used to test the context extraction capabilities of
the second model in the project.
The application dataset consists of papers and other scientific writings where
the citations have not been extracted. This dataset will be significantly smaller
in comparison to the training data and, for the purpose of this project, will
contain examples of cross referencing.

## Methods / Models

To enable our graph creation we will start with a basic reference tree builder
which builds a graph from a dataset which already includes metadata including
the edges. With that graph we will fit a pretrained distilBERT such that it
will be able to, from text only, create the needed metadata for creating a graph.
Furthermore we will fit a BART such that it finds out context for how references
are used and score them accordingly to how critically they are viewed and how
strongly claims are backed up.

## Evaluation

We will try to measure our system by making a visualization function for the
graph which then should show some specific works as roots of ”bad practice”
referencing which we hid within the database. The overall structure should not
be taken as a fully fetched version but more as a proof of concept.



## Restrictions
inline citations only marked with superscript numbers e.g. "argument²" or "other argument³"


{'premise': 'NCIP incubation period to be 5.2 days (Li et al., 2020).', 'argument': 'The incubation period of NCIP is estimated to be about 5.2 days.', 'label': 'SUPPORTS', 'confidence': 0.9999999999977534, 'label_scores': {'SUPPORTS': np.float32(-317.91794), 'CONTRADICTS': np.float32(-344.82513), 'NOT_ENOUGH_INFORMATION': np.float32(-347.24002)}, 'stress_test': {'original_argument_label': 'SUPPORTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}

{'premise': 'We follow Niven and Kao (2019) and report the median for 5 independent runs, as BERT-based models can degenerate.', 'argument': 'Since Bert based models can degenerate it is a practice to report the median of indepent runs.', 'label': 'SUPPORTS', 'confidence': 1.0, 'label_scores': {'SUPPORTS': np.float32(-415.11478), 'CONTRADICTS': np.float32(-454.00778), 'NOT_ENOUGH_INFORMATION': np.float32(-463.35843)}, 'stress_test': {'original_argument_label': 'SUPPORTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}

{'premise': 'Concretely, we set the supervision to be of cell selection if p a (op 0 ) ≥ S, where 0 < S < 1 is a threshold hyperparameter, and the scalar answer supervision otherwise. This follows hard EM (Min et al., 2019), as for spurious programs we pick the most probable one according to the current model.', 'argument': 'Hard EM commits to a models most probable program by switching supervision if the probability of a specific operation exceeds a certain threshold.', 'label': 'SUPPORTS', 'confidence': 0.999999999999996, 'label_scores': {'SUPPORTS': np.float32(-628.29895), 'CONTRADICTS': np.float32(-661.4308), 'NOT_ENOUGH_INFORMATION': np.float32(-673.5592)}, 'stress_test': {'original_argument_label': 'SUPPORTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}

{'premise': 'In recent years, word embeddings (Mikolov et al., 2013; Pennington et al., 2014; Peters et al., 2018; Devlin et al., 2019) have emerged as a commonly used alternative to n-gram matching for capturing word semantics similarity.', 'argument': 'Word embeddings are commonly used for capturing word semantivs similarity.', 'label': 'SUPPORTS', 'confidence': 0.9999919678931832, 'label_scores': {'SUPPORTS': np.float32(-385.18378), 'CONTRADICTS': np.float32(-482.54062), 'NOT_ENOUGH_INFORMATION': np.float32(-396.91583)}, 'stress_test': {'original_argument_label': 'SUPPORTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}

{'premise': 'In recent years, word embeddings (Mikolov et al., 2013; Pennington et al., 2014; Peters et al., 2018; Devlin et al., 2019) have emerged as a commonly used alternative to n-gram matching for capturing word semantics similarity.', 'argument': 'Word embeddings are not used for capturing word semantivs similarity.', 'label': 'NOT_ENOUGH_INFORMATION', 'confidence': 0.9051495158198641, 'label_scores': {'SUPPORTS': np.float32(-477.5546), 'CONTRADICTS': np.float32(-401.0429), 'NOT_ENOUGH_INFORMATION': np.float32(-398.7871)}, 'stress_test': {'original_argument_label': 'NOT_ENOUGH_INFORMATION', 'negated_argument_label': 'SUPPORTS', 'logically_stable': True}}

{'premise': 'In recent years, word embeddings (Mikolov et al., 2013; Pennington et al., 2014; Peters et al., 2018; Devlin et al., 2019) have emerged as a commonly used alternative to n-gram matching for capturing word semantics similarity.', 'argument': 'Word embeddings are never used for capturing word semantivs similarity.', 'label': 'SUPPORTS', 'confidence': 0.625771353624314, 'label_scores': {'SUPPORTS': np.float32(-395.3728), 'CONTRADICTS': np.float32(-402.6115), 'NOT_ENOUGH_INFORMATION': np.float32(-395.88812)}, 'stress_test': {'original_argument_label': 'NOT_ENOUGH_INFORMATION', 'negated_argument_label': 'SUPPORTS', 'logically_stable': True}}

{'premise': 'NCIP incubation period to be 5.2 days (Li et al., 2020).', 'argument': 'The incubation period of NCIP is estimated to be about 52 days.', 'label': 'CONTRADICTS', 'confidence': 0.9999999999945048, 'label_scores': {'SUPPORTS': np.float32(-370.14206), 'CONTRADICTS': np.float32(-344.02322), 'NOT_ENOUGH_INFORMATION': np.float32(-371.69647)}, 'stress_test': {'original_argument_label': 'CONTRADICTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}

{'premise': 'NCIP incubation period to be 5.2 days (Li et al., 2020).', 'argument': 'The incubation period of NCIP is estimated to be two weeks.', 'label': 'CONTRADICTS', 'confidence': 0.9999999999133833, 'label_scores': {'SUPPORTS': np.float32(-341.3217), 'CONTRADICTS': np.float32(-318.10458), 'NOT_ENOUGH_INFORMATION': np.float32(-344.3433)}, 'stress_test': {'original_argument_label': 'CONTRADICTS', 'negated_argument_label': 'CONTRADICTS', 'logically_stable': True}}
PS C:\Users\User\Desktop\Julian\Uni\WS 25\AIR\herBERT>