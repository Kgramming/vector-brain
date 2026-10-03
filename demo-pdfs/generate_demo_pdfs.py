#!/usr/bin/env python3
"""Generate 3 realistic demo PDFs for the Vector-Brain second-brain demo.

Each PDF is a substantive educational chapter (8-12 pages) with definitions,
worked numeric examples, bullet lists, tables, and per-chapter key takeaways,
so cross-document semantic search returns meaningful, citable passages.
"""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, ListFlowable, ListItem,
)
from reportlab.lib import colors

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- styles ---
BODY = ParagraphStyle('body', fontName='Helvetica', fontSize=10.5, leading=15.5,
                      alignment=TA_JUSTIFY, spaceAfter=7, textColor=HexColor('#1F2937'))
TITLE_S = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=24, leading=29,
                         alignment=TA_CENTER, spaceAfter=6, textColor=HexColor('#111827'))
SUBTITLE_S = ParagraphStyle('subtitle', fontName='Helvetica-Oblique', fontSize=12.5, leading=17,
                            alignment=TA_CENTER, spaceAfter=22, textColor=HexColor('#4B5563'))
H1 = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=16, leading=20,
                    spaceBefore=16, spaceAfter=8, textColor=HexColor('#1E3A8A'),
                    keepWithNext=True)
H2 = ParagraphStyle('h2', fontName='Helvetica-Bold', fontSize=12.5, leading=16,
                    spaceBefore=11, spaceAfter=6, textColor=HexColor('#374151'),
                    keepWithNext=True)
BULLET = ParagraphStyle('bullet', parent=BODY, alignment=TA_LEFT, leftIndent=20,
                        firstLineIndent=0, bulletIndent=8, spaceAfter=4)
CAPTION = ParagraphStyle('caption', fontName='Helvetica-Oblique', fontSize=9,
                         leading=12.5, alignment=TA_CENTER, spaceBefore=4,
                         spaceAfter=10, textColor=HexColor('#6B7280'))
TAKE_S = ParagraphStyle('takeaway', fontName='Helvetica', fontSize=10, leading=14.5,
                        textColor=HexColor('#1E1B4B'))
FOOT_S = ParagraphStyle('foot', fontName='Helvetica', fontSize=8.5,
                        textColor=HexColor('#9CA3AF'), alignment=TA_CENTER)

ACCENT = HexColor('#4F46E5')


def p(text):
    return Paragraph(text, BODY)


def h1(text):
    return Paragraph(text, H1)


def h2(text):
    return Paragraph(text, H2)


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(it, BULLET), leftIndent=20, bulletColor=ACCENT)
         for it in items],
        bulletType='bullet', start='circle', leftIndent=20)


def takeaway(title, items):
    inner = '<b>' + title + '</b><br/>' + '<br/>'.join('&bull;&nbsp;&nbsp;' + s for s in items)
    t = Table([[Paragraph(inner, TAKE_S)]], colWidths=[6.3 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#EEF2FF')),
        ('BOX', (0, 0), (-1, -1), 0.8, ACCENT),
        ('LINEBELOW', (0, 0), (-1, 0), 0, colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    return [Spacer(1, 6), t, Spacer(1, 10)]


def datatable(headers, rows, caption=None):
    data = [[Paragraph('<b>' + h + '</b>', BODY)] + [] for h in []]  # placeholder
    hdr = [Paragraph('<b><font color="#FFFFFF">' + h + '</font></b>', BODY) for h in headers]
    body = [[Paragraph(str(c), BODY) for c in row] for row in rows]
    t = Table([hdr] + body, repeatRows=1,
              colWidths=[(6.5 * inch) / len(headers)] * len(headers))
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3730A3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#C7D2FE')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    for i in range(1, len(body) + 1):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), HexColor('#F5F3FF')))
    t.setStyle(TableStyle(style))
    out = [t]
    if caption:
        out.append(Paragraph(caption, CAPTION))
    return out


def spacer(h=8):
    return Spacer(1, h)


def footer(doc_title):
    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8.5)
        canvas.setFillColor(HexColor('#9CA3AF'))
        canvas.drawCentredString(4.25 * inch, 0.55 * inch,
                                 '%s  |  Page %d' % (doc_title, doc.page))
        canvas.restoreState()
    return _draw


def build_pdf(filename, doctitle, subtitle, story):
    path = os.path.join(OUTDIR, filename)
    doc = SimpleDocTemplate(path, pagesize=LETTER,
                            leftMargin=0.95 * inch, rightMargin=0.95 * inch,
                            topMargin=0.85 * inch, bottomMargin=0.85 * inch,
                            title=doctitle, author='Vector-Brain Demo Corpus')
    full = [Paragraph(doctitle, TITLE_S), Paragraph(subtitle, SUBTITLE_S),
            Spacer(1, 6)] + story
    doc.build(full, onFirstPage=footer(doctitle), onLaterPages=footer(doctitle))
    return path


# ============================================================ PDF 1 ========
def story_ml_intro():
    s = []
    s.append(h1('Chapter 1: What Is Machine Learning?'))
    s.append(p(
        'Machine learning is a subfield of artificial intelligence in which computer '
        'programs improve their performance on a task through experience, rather than '
        'through explicitly programmed rules. The classic formulation comes from Tom '
        'Mitchell (1997): a program is said to learn from experience E with respect to '
        'some class of tasks T and performance measure P, if its performance at tasks '
        'in T, as measured by P, improves with experience E.'))
    s.append(p(
        'Consider a spam filter. A traditional program would need a programmer to '
        'hand-write rules such as "if the subject contains FREE MONEY, mark as spam." '
        'Those rules break constantly, because spammers adapt. A machine learning '
        'approach instead feeds the program thousands of labeled emails (the experience E), '
        'asks it to predict spam versus not-spam (the task T), and measures the fraction '
        'of correct predictions (the performance measure P). The program adjusts its '
        'internal parameters to do better on the next batch of emails it sees.'))
    s.append(p(
        'What makes this powerful is generalization: the ability to make sensible '
        'predictions on data the program has never seen before. A model that merely '
        'memorizes its training emails would fail on new ones. Learning, in the machine '
        'learning sense, means discovering patterns that hold beyond the specific '
        'examples used for training.'))
    s.append(h2('Why not just write rules?'))
    s.append(p(
        'Rule-based systems work well when the decision logic is crisp and stable, like '
        'tax calculations. They fail when the input is messy, high-dimensional, or '
        'constantly shifting: recognizing speech, reading handwriting, recommending '
        'movies, or detecting fraud. In these domains, humans cannot articulate the '
        'exact rules they themselves follow — you recognize your friend\'s face '
        'instantly but cannot write down the pixel-level rule that does it. Machine '
        'learning sidesteps this by learning the decision boundary directly from data.'))
    s.append(bullets([
        '<b>Data-driven:</b> behavior is shaped by examples, not by hand-coded logic.',
        '<b>Adaptive:</b> retraining on fresh data lets the model track a changing world.',
        '<b>Probabilistic:</b> predictions usually come with uncertainty, not certainties.',
        '<b>Evaluated empirically:</b> we judge models by measured performance on held-out data, not by elegance of code.',
    ]))
    s.append(p(
        'A running theme of this document is that machine learning is less about fancy '
        'algorithms and more about disciplined experimentation: choosing the right '
        'problem formulation, preparing representative data, selecting a model family, '
        'and evaluating honestly. The mathematics matters, but judgment about data and '
        'evaluation is what separates working systems from impressive demos.'))
    s.extend(takeaway('Chapter 1 - Key Takeaways', [
        'Machine learning programs improve at a task T, measured by P, through experience E.',
        'Generalization to unseen data is the entire point; memorization is not learning.',
        'Use ML when rules are hard to articulate or the environment keeps changing.',
        'ML is an empirical discipline: measure on held-out data, not on training data.',
    ]))

    s.append(h1('Chapter 2: Supervised, Unsupervised, and Reinforcement Learning'))
    s.append(p(
        'Machine learning problems are usually grouped into three paradigms, distinguished '
        'by what kind of feedback the learner receives. The distinction matters because '
        'it determines which algorithms apply and how you evaluate success.'))
    s.append(h2('Supervised learning: learning from labeled examples'))
    s.append(p(
        'In supervised learning, each training example comes with the correct answer, '
        'called the label. The model\'s job is to learn a mapping from inputs to labels '
        'so it can label new inputs. If the label is a continuous number — house price, '
        'tomorrow\'s temperature — the task is called regression. If the label is one of '
        'a fixed set of categories — spam or not spam, cat / dog / bird — the task is '
        'called classification.'))
    s.append(p(
        'A concrete regression example: a real-estate dataset with 200 past sales, each '
        'recording living area in square feet and sale price. The model learns a function '
        'mapping area to price. A concrete classification example: 10,000 customer support '
        'tickets labeled "billing", "technical", or "account", used to train a router that '
        'sends new tickets to the right team.'))
    s.append(h2('Unsupervised learning: finding structure without labels'))
    s.append(p(
        'In unsupervised learning there are no labels — only raw inputs — and the goal '
        'is to discover structure. Clustering groups similar items: a retailer might '
        'cluster customers into segments based on purchase history without anyone '
        'pre-defining the segments. Dimensionality reduction compresses high-dimensional '
        'data into fewer dimensions while preserving the important variation; it is '
        'widely used for visualization and as a preprocessing step. Anomaly detection '
        'flags rare, unusual points, which is the backbone of credit-card fraud systems.'))
    s.append(h2('Reinforcement learning: learning from rewards'))
    s.append(p(
        'In reinforcement learning an agent takes actions in an environment and receives '
        'rewards or penalties. There are no correct answers supplied; the agent must '
        'discover, by trial and error, a policy — a strategy for choosing actions — that '
        'maximizes cumulative reward. Game-playing systems, robotics controllers, and '
        'recommendation engines that optimize long-term engagement are classic '
        'applications. Reinforcement learning is powerful but sample-hungry and harder '
        'to evaluate than supervised learning, so most production ML systems you meet '
        'will be supervised.'))
    s.extend(datatable(
        ['Paradigm', 'Feedback signal', 'Typical tasks', 'Example'],
        [['Supervised', 'Labeled examples (input + correct answer)',
          'Regression, classification', 'Predict house prices from area'],
         ['Unsupervised', 'No labels; raw data only',
          'Clustering, anomaly detection', 'Segment customers by behavior'],
         ['Reinforcement', 'Rewards / penalties for actions',
          'Control, game play', 'Teach a robot arm to grasp objects']],
        caption='Table 1: The three learning paradigms compared.'))
    s.extend(takeaway('Chapter 2 - Key Takeaways', [
        'Supervised learning maps inputs to known labels: regression for numbers, classification for categories.',
        'Unsupervised learning discovers structure (clusters, anomalies) with no labels at all.',
        'Reinforcement learning optimizes actions through reward feedback, not correct answers.',
        'Most real-world ML products are supervised; pick the paradigm that matches your feedback signal.',
    ]))
    return s

def story_ml_intro_ch3_6():
    s = []
    s.append(h1('Chapter 3: Regression - Predicting Numbers'))
    s.append(p(
        'Regression is the supervised learning task of predicting a continuous numeric '
        'value. House prices, energy demand, delivery times, and crop yields are all '
        'regression targets. The simplest and most instructive model is linear '
        'regression, which assumes the target is approximately a straight-line function '
        'of the input features.'))
    s.append(h2('Linear regression'))
    s.append(p(
        'With a single feature, the model is y = w * x + b: the prediction y is the '
        'feature x scaled by a weight w and shifted by a bias b. Geometrically this is '
        'a line; learning means choosing the slope w and intercept b that fit the data '
        'best. With multiple features the line becomes a hyperplane, but the idea is '
        'identical: prediction equals a weighted sum of features plus a bias term.'))
    s.append(h2('The cost function: how wrong are we?'))
    s.append(p(
        'To choose w and b we need a number that says how bad the current line is. The '
        'standard choice is the mean squared error (MSE): for each training point, take '
        'the prediction error (predicted minus actual), square it, and average over all '
        'points. Squaring does two useful things: it makes all errors positive, and it '
        'punishes large errors disproportionately — being off by 10 costs one hundred '
        'times more than being off by 1, which pushes the model to avoid big misses.'))
    s.append(p(
        'Worked mini-example. Three houses: areas 1000, 1500, 2000 sq ft with prices '
        '150, 200, 280 (in thousands). Suppose our line is y = 0.12 * x + 20. Predictions: '
        '140, 200, 260. Errors: -10, 0, -20. Squared errors: 100, 0, 400. MSE = '
        '(100 + 0 + 400) / 3 = 166.7. A competing line y = 0.13 * x + 15 gives predictions '
        '145, 210, 275; squared errors 25, 100, 25; MSE = 50. The second line wins '
        'because its cost is lower. Learning is the search for the line with the '
        'lowest cost.'))
    s.append(h2('Gradient descent: walking downhill'))
    s.append(p(
        'Gradient descent is the workhorse optimizer behind most of machine learning. '
        'Picture the cost as a valley: the horizontal axes are the parameters (w and b) '
        'and the height is the cost. Start somewhere on the hillside, compute which '
        'direction slopes downward steepest (the negative gradient), take a small step '
        'that way, and repeat. Each step lowers the cost until you settle at the '
        'bottom of the valley.'))
    s.append(p(
        'The step size is called the learning rate. Too large, and you leap over the '
        'valley and bounce around or diverge; too small, and training crawls. Choosing '
        'the learning rate is one of the most consequential practical decisions in '
        'training any model. For plain linear regression there is also a closed-form '
        'solution (the normal equation), but gradient descent generalizes to models '
        'with millions of parameters where no closed form exists — including the neural '
        'networks covered in the companion document on deep learning.'))
    s.extend(takeaway('Chapter 3 - Key Takeaways', [
        'Linear regression predicts a number as a weighted sum of features plus bias.',
        'Mean squared error turns "how wrong" into a single number; squaring punishes large errors most.',
        'Gradient descent repeatedly steps downhill on the cost surface; the learning rate controls step size.',
        'Closed-form solutions exist for linear regression, but gradient descent scales to far bigger models.',
    ]))

    s.append(h1('Chapter 4: Classification - Predicting Categories'))
    s.append(p(
        'Classification assigns each input to one of a fixed set of classes: spam or '
        'not spam, benign or malignant, churned or retained. The output is discrete, '
        'which changes both the model and how we measure success. A natural first '
        'instinct is to reuse linear regression and round its output, but probabilities '
        'need to stay between 0 and 1, and a straight line cannot do that gracefully.'))
    s.append(h2('Logistic regression'))
    s.append(p(
        'Despite its name, logistic regression is a classification algorithm. It computes '
        'the same weighted sum as linear regression, z = w * x + b, then squeezes it '
        'through the sigmoid (logistic) function, which maps any real number into the '
        'range 0 to 1. The output is interpreted as the probability of belonging to the '
        'positive class. A threshold — usually 0.5 — converts the probability into a '
        'hard decision: above the threshold, predict class 1; below it, predict class 0.'))
    s.append(h2('Decision boundaries'))
    s.append(p(
        'The decision boundary is the surface in feature space where the model switches '
        'its prediction from one class to another. For logistic regression with two '
        'features, the boundary is a straight line: points on one side are classified '
        'positive, points on the other negative. This is why logistic regression is '
        'called a linear classifier — its boundary is linear even though its output is '
        'a probability. When classes are intertwined like two interleaved crescents, no '
        'straight line separates them, and a linear model underfits; that limitation is '
        'exactly what motivates richer models such as decision trees and neural networks.'))
    s.append(p(
        'Worked mini-example. A bank scores loan applicants with z = 0.02 * income '
        '(in thousands) - 0.5 * missed_payments - 1. Applicant A: income 80, missed 0, '
        'so z = 1.6 - 0 - 1 = 0.6, sigmoid gives about 0.65 — approve (above 0.5). '
        'Applicant B: income 40, missed 3, so z = 0.8 - 1.5 - 1 = -1.7, sigmoid gives '
        'about 0.15 — reject. Moving the threshold to 0.7 would make the bank stricter: '
        'fewer approvals, fewer defaults, but also fewer good customers accepted. That '
        'tradeoff between kinds of errors is the subject of the evaluation document.'))
    s.extend(takeaway('Chapter 4 - Key Takeaways', [
        'Logistic regression outputs a probability via the sigmoid; a threshold turns it into a class.',
        'The decision boundary is where the prediction flips; for logistic regression it is linear.',
        'Linear classifiers underfit data whose classes are not linearly separable.',
        'Moving the decision threshold trades one kind of error against another.',
    ]))

    s.append(h1('Chapter 5: Overfitting and Underfitting'))
    s.append(p(
        'A model with too little capacity misses real patterns — it underfits. A model '
        'with too much capacity memorizes noise — it overfits. Imagine fitting curves '
        'to ten noisy points sampled from a gentle parabola. A straight line underfits: '
        'it cannot bend at all. A degree-9 polynomial overfits: it threads every point '
        'exactly but oscillates wildly between them, and its predictions on new points '
        'are terrible. A quadratic curve gets it about right.'))
    s.append(h2('The bias-variance tradeoff'))
    s.append(p(
        'Underfitting is high bias: the model\'s assumptions are so rigid that it '
        'systematically misses the truth, and its predictions are stable but wrong. '
        'Overfitting is high variance: the model is so flexible that small changes in '
        'the training data produce very different models, and predictions swing with '
        'the noise. Total error decomposes, roughly, into bias squared plus variance '
        'plus irreducible noise — you cannot drive both terms to zero simultaneously by '
        'tuning capacity alone. The practical goal is the sweet spot in the middle, '
        'found by honest evaluation rather than by theory.'))
    s.append(h2('Regularization: a penalty for complexity'))
    s.append(p(
        'Regularization fights overfitting by adding a penalty for large weights to the '
        'cost function. The model must now balance fitting the data against keeping '
        'weights small. L2 regularization (ridge) penalizes the sum of squared weights, '
        'shrinking all of them smoothly toward zero. L1 regularization (lasso) penalizes '
        'the sum of absolute weights, which tends to drive some weights exactly to zero '
        '— effectively performing feature selection. The strength of the penalty is a '
        'hyperparameter, usually chosen by cross-validation.'))
    s.append(bullets([
        '<b>More training data</b> almost always reduces overfitting; it is the most reliable cure.',
        '<b>Simpler models</b> (fewer features, shallower trees) underfit less-flexible alternatives less often.',
        '<b>Early stopping</b> halts training when validation error starts rising.',
        '<b>Dropout and data augmentation</b> are regularization tools especially popular in deep learning.',
    ]))
    s.extend(takeaway('Chapter 5 - Key Takeaways', [
        'Underfitting = high bias (too rigid); overfitting = high variance (memorizes noise).',
        'Judge models on held-out data: training error alone cannot reveal overfitting.',
        'Regularization penalizes large weights; L1 can zero out features, L2 shrinks them smoothly.',
        'More data, simpler models, and early stopping are the standard defenses.',
    ]))

    s.append(h1('Chapter 6: Model Evaluation Basics'))
    s.append(p(
        'Evaluation answers one question: how will this model perform on data it has not '
        'seen? Everything else — fancy architectures, clever features — is secondary to '
        'measuring this honestly. The cardinal sin is evaluating on the same data used '
        'for training, which rewards memorization and tells you nothing about the future.'))
    s.append(h2('Train / validation / test splits'))
    s.append(p(
        'Split the data into three parts. Train on the training set. Tune '
        'hyperparameters (learning rate, regularization strength, tree depth) against '
        'the validation set. Report final performance exactly once on the test set, '
        'which must remain untouched until the end — peeking at it during development '
        'leaks information and inflates the reported score. A common split is '
        '70 / 15 / 15, though ratios vary with dataset size.'))
    s.append(h2('Cross-validation'))
    s.append(p(
        'When data is scarce, a single split is noisy: your score depends on the luck '
        'of which points landed in the test set. K-fold cross-validation partitions the '
        'data into K equal folds, trains on K-1 folds, evaluates on the remaining fold, '
        'and repeats K times so every point is tested exactly once. The average score '
        'is a far more stable estimate. Five or ten folds are standard; the price is '
        'training K models instead of one.'))
    s.append(h2('Accuracy and its limits'))
    s.append(p(
        'Accuracy — the fraction of correct predictions — is the most intuitive metric, '
        'and often a misleading one. A fraud detector on data with 99 percent legitimate '
        'transactions scores 99 percent accuracy by predicting "legitimate" for '
        'everything, while catching zero fraud. When classes are imbalanced or when '
        'different errors have different costs, accuracy hides the failures that matter. '
        'The companion document on evaluation develops the full toolkit — confusion '
        'matrices, precision, recall, F1, and ROC curves — that replaces naive accuracy.'))
    s.extend(takeaway('Chapter 6 - Key Takeaways', [
        'Evaluate on held-out data; training accuracy measures memorization, not learning.',
        'Keep a pristine test set; tune hyperparameters on a separate validation set.',
        'K-fold cross-validation gives stabler estimates when data is scarce.',
        'Accuracy misleads on imbalanced data — richer metrics are covered in the evaluation document.',
    ]))
    return s

# ============================================================ PDF 2 ========
def story_nn_deep():
    s = []
    s.append(h1('Chapter 1: The Artificial Neuron'))
    s.append(p(
        'The artificial neuron is the atomic unit of neural networks, loosely inspired '
        'by biological neurons but best understood as a tiny mathematical device. It '
        'receives several numeric inputs, multiplies each by a weight, adds them up, '
        'adds a bias term, and passes the result through an activation function. In '
        'symbols: output = f(w1*x1 + w2*x2 + ... + wn*xn + b), where f is the activation '
        'function covered in the next chapter.'))
    s.append(p(
        'Each piece has a job. The weights decide how much attention the neuron pays to '
        'each input — a large positive weight means "this input pushes the output up," '
        'a negative weight means "this input pushes it down," and a near-zero weight '
        'means "ignore this input." The bias shifts the whole response up or down, '
        'letting the neuron fire even when all inputs are zero, or stay silent despite '
        'strong inputs. Learning a neural network means finding the right weights and '
        'biases; the architecture — how neurons are wired together — is chosen by the '
        'designer.'))
    s.append(h2('A neuron, computed by hand'))
    s.append(p(
        'Take a neuron with two inputs, weights w1 = 0.5 and w2 = -0.8, bias b = 0.3, '
        'and for now a simple step activation: output 1 if the sum is positive, else 0. '
        'Feed it x1 = 2.0, x2 = 1.0. Weighted sum: 0.5*2.0 + (-0.8)*1.0 + 0.3 = '
        '1.0 - 0.8 + 0.3 = 0.5. Positive, so the neuron fires: output 1. Now feed it '
        'x1 = 0.5, x2 = 2.0: sum = 0.25 - 1.6 + 0.3 = -1.05. Negative — the neuron stays '
        'silent: output 0. One neuron implements a linear decision boundary, exactly '
        'like logistic regression; the power of neural networks comes from composing '
        'many such units into layers.'))
    s.append(p(
        'A single neuron is a linear model wearing a costume. Stack neurons into a '
        'hidden layer, feed their outputs into another layer, and the composition '
        'becomes capable of carving highly non-linear decision boundaries — provided '
        'the activation functions between layers are non-linear. With purely linear '
        'activations, any stack of layers collapses mathematically into a single '
        'layer, no matter how deep. Non-linearity is the whole game.'))
    s.extend(takeaway('Chapter 1 - Key Takeaways', [
        'A neuron computes f(weighted sum of inputs + bias); weights are learned, architecture is designed.',
        'Weights scale each input\'s influence; the bias shifts the activation threshold.',
        'One neuron is a linear classifier; depth plus non-linearity creates expressive power.',
        'A stack of linear layers collapses to one layer — non-linear activations are essential.',
    ]))

    s.append(h1('Chapter 2: Activation Functions'))
    s.append(p(
        'The activation function decides what a neuron outputs given its weighted sum. '
        'Historically the sigmoid was standard; today the rectified linear unit (ReLU) '
        'dominates hidden layers. The choice matters enormously: it determines what '
        'functions the network can represent and whether gradients flow during training.'))
    s.append(h2('Sigmoid and tanh'))
    s.append(p(
        'The sigmoid squashes any input into the range 0 to 1, which made it natural '
        'for interpreting outputs as probabilities. The hyperbolic tangent (tanh) is a '
        'rescaled sibling squashing into -1 to 1, centered at zero, which often trains '
        'a little better. Both share a fatal flaw for deep networks: saturation. For '
        'large positive or negative inputs their curves flatten, the derivative drops '
        'near zero, and gradients vanish — early layers stop learning. This vanishing '
        'gradient problem is a central reason deep networks were hard to train before '
        'ReLU.'))
    s.append(h2('ReLU and its variants'))
    s.append(p(
        'ReLU is disarmingly simple: output the input if positive, else zero. It does '
        'not saturate for positive values, so gradients flow undiminished; it is cheap '
        'to compute; and it induces sparsity, since many neurons output exactly zero. '
        'Its weakness is the "dying ReLU": a neuron whose weighted sum is always '
        'negative outputs zero forever, its gradient is zero, and it never recovers. '
        'Leaky ReLU fixes this with a small slope (often 0.01) for negative inputs, '
        'letting a trickle of gradient through. In practice, plain ReLU with careful '
        'initialization works well enough that it remains the default.'))
    s.append(h2('Softmax: turning scores into probabilities'))
    s.append(p(
        'For multi-class classification the final layer typically uses softmax, which '
        'converts a vector of raw scores into a probability distribution: each output '
        'is between 0 and 1 and they sum to 1. Unlike the element-wise functions above, '
        'softmax is computed across the whole output vector — raising one class\'s '
        'probability necessarily lowers the others\', which matches the "exactly one '
        'correct class" assumption. Rule of thumb: ReLU (or a variant) in hidden '
        'layers, sigmoid for binary outputs, softmax for multi-class outputs, and no '
        'activation (a linear output) for regression.'))
    s.extend(takeaway('Chapter 2 - Key Takeaways', [
        'Sigmoid and tanh saturate, causing vanishing gradients in deep networks.',
        'ReLU (max(0, x)) keeps gradients alive for positive inputs and is the hidden-layer default.',
        'Leaky ReLU prevents dead neurons with a small negative slope.',
        'Softmax converts output scores into a proper probability distribution for multi-class tasks.',
    ]))

    s.append(h1('Chapter 3: Network Architectures'))
    s.append(p(
        'The multi-layer perceptron (MLP) — also called a feedforward network — wires '
        'neurons in layers: an input layer, one or more hidden layers, and an output '
        'layer, with every neuron in one layer connected to every neuron in the next. '
        'Information flows strictly forward. Despite its simplicity, an MLP with a '
        'single sufficiently wide hidden layer can approximate any continuous function '
        '— the universal approximation theorem. The catch is "sufficiently wide" might '
        'mean impractically wide; depth buys representational efficiency.'))
    s.append(h2('Depth versus width'))
    s.append(p(
        'Depth (more layers) lets the network build hierarchical features: in image '
        'networks, early layers detect edges, middle layers assemble parts, and late '
        'layers recognize objects. Width (more neurons per layer) increases capacity '
        'within a single level of abstraction. Empirically, deep-and-narrow usually '
        'beats shallow-and-wide for structured data like images, text, and audio, '
        'because the world itself is compositional. But depth brings optimization '
        'challenges — vanishing and exploding gradients — which is why architectural '
        'innovations like residual connections (skip connections that let gradients '
        'bypass layers) were breakthroughs.'))
    s.append(p(
        'Beyond MLPs, the architecture zoo includes convolutional networks for grid-like '
        'data (Chapter 6), recurrent networks and transformers for sequences, and '
        'autoencoders and GANs for unsupervised and generative tasks. The unifying '
        'principle: bake the structure of your data into the architecture. Convolutions '
        'encode "nearby pixels relate"; recurrence encodes "order matters." Choosing '
        'architecture is choosing inductive bias — what the network finds easy to learn.'))
    s.extend(takeaway('Chapter 3 - Key Takeaways', [
        'MLPs connect every neuron to the next layer; one wide hidden layer can approximate any function in theory.',
        'Depth builds hierarchical features; deep-and-narrow usually beats shallow-and-wide on structured data.',
        'Residual skip connections made very deep networks trainable.',
        'Architecture choice is inductive bias: match the wiring to the structure of your data.',
    ]))

    s.append(h1('Chapter 4: Backpropagation'))
    s.append(p(
        'Backpropagation is the algorithm that makes training deep networks feasible. '
        'Training needs, for every weight in the network, the answer to: "if I nudge '
        'this weight slightly, how does the final error change?" With millions of '
        'weights, computing each gradient naively would be impossibly slow. '
        'Backpropagation computes all of them in roughly the cost of two passes '
        'through the network by reusing intermediate results via the chain rule.'))
    s.append(h2('Forward pass, then backward pass'))
    s.append(p(
        'First the forward pass: feed an input through the network, layer by layer, '
        'caching each layer\'s weighted sums and activations, and compute the loss at '
        'the end. Then the backward pass walks the computation in reverse. At the '
        'output layer we know directly how the loss changes with the final activations. '
        'The chain rule lets us propagate that sensitivity backward: the gradient at '
        'layer L tells us the gradient at layer L-1, which tells us layer L-2, and so '
        'on. Each layer\'s weight gradients are then just the product of the error '
        'signal arriving at that layer and the inputs it saw during the forward pass.'))
    s.append(h2('Chain rule intuition'))
    s.append(p(
        'A tiny numeric sketch. Suppose loss = (y - target)^2 with target 1.0, and the '
        'network output y = 0.7, so loss = 0.09. The derivative of loss with respect to '
        'y is 2*(0.7 - 1.0) = -0.6: increasing y decreases the loss. If y = sigmoid(z) '
        'with z = 0.85, then dy/dz = y*(1-y) = 0.21. Chain rule: dLoss/dz = '
        '-0.6 * 0.21 = -0.126. If z = w*x with x = 2.0, then dLoss/dw = -0.126 * 2.0 = '
        '-0.252. Since the gradient is negative, increasing w reduces the loss — so '
        'gradient descent will nudge w upward. Backpropagation is this bookkeeping, '
        'automated, for every parameter at once. Modern frameworks build the backward '
        'pass automatically from the forward code (autodiff); nobody hand-derives these '
        'by hand anymore, but the intuition — error signals flowing backward, split by '
        'the chain rule — explains every training trick in the book.'))
    s.append(p(
        'This is also where the connection to gradient descent becomes explicit: '
        'backpropagation is not an optimizer. It is an efficient gradient computer. '
        'Gradient descent (and its variants from the next chapter) is what decides how '
        'to step using those gradients. Backprop answers "which direction is downhill"; '
        'the optimizer decides "how far to walk."'))
    s.extend(takeaway('Chapter 4 - Key Takeaways', [
        'Backpropagation computes all weight gradients in about two network passes using the chain rule.',
        'Forward pass caches activations; backward pass propagates error signals from output to input.',
        'Backprop is a gradient computer, not an optimizer — gradient descent decides the step.',
        'Automatic differentiation builds the backward pass from forward code; hand-derivation is obsolete.',
    ]))
    return s

def story_nn_deep_ch5_7():
    s = []
    s.append(h1('Chapter 5: Optimization - From SGD to Adam'))
    s.append(p(
        'Backpropagation tells us the downhill direction; the optimizer decides how to '
        'move. Plain gradient descent computes the gradient over the entire dataset '
        'before taking one step — accurate but glacial on large data. Stochastic '
        'gradient descent (SGD) instead estimates the gradient from a small random '
        'mini-batch (typically 32 to 256 examples) and steps far more often. The '
        'estimate is noisy, but the noise averages out, and the sheer number of steps '
        'wins: SGD sees far more updates per hour of compute.'))
    s.append(h2('Momentum: remembering the direction'))
    s.append(p(
        'Picture a long narrow valley: plain SGD zigzags across the walls, wasting '
        'effort. Momentum adds a velocity term — each step keeps a fraction (often '
        '0.9) of the previous step\'s direction and adds the new gradient. Consistent '
        'directions accumulate into fast progress along the valley floor while '
        'oscillations cancel out. It is the difference between a marble rolling with '
        'inertia and one that stops dead at every measurement.'))
    s.append(h2('Adaptive methods and Adam'))
    s.append(p(
        'Different parameters often need different step sizes: sparse features want '
        'big steps, dense features want small ones. Adaptive optimizers give each '
        'parameter its own learning rate, scaled by the history of its gradients. '
        'Adam — adaptive moment estimation — combines momentum with per-parameter '
        'adaptive rates, plus bias correction for the early steps when the running '
        'averages are still warming up. It is the default starting choice for most '
        'deep learning work because it is forgiving of the learning-rate setting.'))
    s.append(h2('Learning rates and schedules'))
    s.append(p(
        'No optimizer rescues a bad learning rate. Too high: the loss explodes or '
        'oscillates. Too low: training takes forever and can get stuck in poor sharp '
        'minima. The standard practice is a schedule: start moderate, decay over time '
        '(step decay, cosine annealing), or warm up from small to large in the first '
        'epochs. A practical tip: if the loss does not fall in the first few epochs, '
        'the learning rate is the first knob to check — before blaming the architecture.'))
    s.extend(takeaway('Chapter 5 - Key Takeaways', [
        'SGD trades exact gradients for many cheap noisy steps on mini-batches — and wins on wall-clock time.',
        'Momentum accumulates consistent directions and damps zigzagging in narrow valleys.',
        'Adam combines momentum with per-parameter adaptive learning rates; it is the usual default.',
        'Learning-rate choice and scheduling dominate practical training success.',
    ]))

    s.append(h1('Chapter 6: Convolutional Neural Networks'))
    s.append(p(
        'A 256x256 color image has nearly 200,000 input values. A fully connected layer '
        'would need a weight per input per neuron — millions of parameters before the '
        'network has learned anything, and it would treat a cat in the top-left as '
        'unrelated to a cat in the bottom-right. Convolutional neural networks (CNNs) '
        'exploit two facts about images: nearby pixels are related (locality), and a '
        'pattern means the same thing wherever it appears (translation invariance).'))
    s.append(h2('Kernels: small learned feature detectors'))
    s.append(p(
        'Instead of connecting to the whole image, each CNN neuron looks at a small '
        'patch — say 3x3 pixels — through a kernel (filter): a tiny grid of weights. '
        'The same kernel slides across the entire image, computing a dot product at '
        'each position and producing a feature map that lights up wherever the pattern '
        'appears. Because the kernel is shared across positions, the network needs '
        'only 9 weights to detect horizontal edges everywhere, instead of one set of '
        'weights per location. A layer learns dozens or hundreds of kernels in '
        'parallel: one for edges, one for corners, one for textures, and so on.'))
    s.append(h2('Pooling: shrinking while keeping what matters'))
    s.append(p(
        'Pooling layers downsample feature maps, typically by taking the maximum value '
        'in each 2x2 region (max pooling). This halves the spatial dimensions, cutting '
        'computation for later layers, and adds a degree of translation invariance: if '
        'an edge shifts by one pixel, the pooled output barely changes. The classic '
        'CNN stacks convolution, non-linearity, and pooling repeatedly — early layers '
        'learn edges and blobs, middle layers learn parts like eyes and wheels, late '
        'layers learn whole objects — then flattens into fully connected layers for '
        'the final classification.'))
    s.append(h2('Why CNNs resist overfitting better than MLPs on images'))
    s.append(p(
        'Weight sharing is a massive capacity cut: a CNN reuses the same few thousand '
        'kernel weights across the image instead of learning separate weights per '
        'pixel location. Fewer parameters mean less room to memorize noise, which '
        'directly attacks overfitting — the high-variance failure mode from the '
        'introductory document. Pooling adds further regularization by discarding '
        'precise positional information the network might otherwise overfit to. '
        'Combined with data augmentation (random crops, flips, rotations that teach '
        'invariance explicitly), CNNs generalize from far less data than a fully '
        'connected network ever could on the same images.'))
    s.extend(takeaway('Chapter 6 - Key Takeaways', [
        'CNNs use small shared kernels slid across the image, exploiting locality and translation invariance.',
        'Weight sharing slashes parameter counts versus fully connected layers on images.',
        'Pooling downsamples feature maps, cutting compute and adding shift tolerance.',
        'Fewer parameters plus augmentation is why CNNs overfit less than MLPs on image data.',
    ]))

    s.append(h1('Chapter 7: Training Practicalities'))
    s.append(p(
        'Theory gets you a network; craft gets it trained. A handful of practical '
        'decisions separate networks that converge cleanly from ones that stall, '
        'explode, or memorize.'))
    s.append(h2('Initialization'))
    s.append(p(
        'Starting all weights at zero is a classic bug: every neuron in a layer then '
        'computes the same thing, receives the same gradient, and stays identical '
        'forever — symmetry never breaks. Random initialization breaks symmetry, but '
        'the scale matters: too large and activations explode layer by layer; too '
        'small and signals vanish. Xavier initialization scales weights by layer size '
        'for sigmoid/tanh networks; He initialization does the analogous scaling for '
        'ReLU, accounting for the half of neurons it zeroes out. Modern frameworks '
        'apply these by default — but knowing they exist explains mysterious '
        '"network won\'t train" failures when defaults are overridden.'))
    s.append(h2('Normalization'))
    s.append(p(
        'Networks train best when inputs are on similar scales: standardize features '
        'to zero mean and unit variance, or scale images to the 0-1 range. Batch '
        'normalization goes further, normalizing each layer\'s activations during '
        'training using mini-batch statistics, which smooths the optimization landscape '
        'and permits higher learning rates. It adds slight noise (batch statistics '
        'vary), which doubles as mild regularization.'))
    s.append(h2('Early stopping and the validation curve'))
    s.append(p(
        'Track loss on a held-out validation set as training proceeds. Training loss '
        'falls monotonically, but validation loss eventually bottoms out and starts '
        'rising — the moment the network begins memorizing instead of learning. Early '
        'stopping halts training at the minimum of the validation curve and keeps '
        'that checkpoint. It is the cheapest, most honest regularization available, '
        'and it directly operationalizes the bias-variance tradeoff: stop at the '
        'sweet spot between underfitting (stopped too early) and overfitting (trained '
        'too long). Combined with dropout, weight decay (L2), and augmentation, it '
        'forms the standard anti-overfitting toolkit.'))
    s.extend(takeaway('Chapter 7 - Key Takeaways', [
        'Never initialize all weights to zero; use Xavier for tanh/sigmoid, He for ReLU.',
        'Normalize inputs and consider batch normalization to stabilize training.',
        'Early stopping at the validation-loss minimum is the simplest regularization.',
        'Dropout, weight decay, and augmentation complete the anti-overfitting toolkit.',
    ]))
    return s

# ============================================================ PDF 3 ========
def story_eval():
    s = []
    s.append(h1('Chapter 1: Why Evaluation Matters'))
    s.append(p(
        'A model is a promise about the future, and evaluation is how we check whether '
        'the promise holds. Every modeling decision — which algorithm, which features, '
        'which hyperparameters — should be justified by measured performance on data '
        'the model did not train on. Without rigorous evaluation, machine learning '
        'degenerates into storytelling: impressive training curves that collapse the '
        'moment the model meets the real world.'))
    s.append(p(
        'Consider a hospital triage model that scores 97 percent accuracy in the lab '
        'but was evaluated on the same patients it trained on. Deployed, it misses '
        'critical cases it never truly learned to recognize. The cost of sloppy '
        'evaluation is not an embarrassing demo — it is misdiagnosed patients, '
        'approved bad loans, and undetected fraud. Evaluation is not paperwork that '
        'follows modeling; it is the discipline that makes modeling trustworthy.'))
    s.append(h2('What "good" means depends on the problem'))
    s.append(p(
        'There is no single number that captures model quality. A spam filter that '
        'occasionally lets spam through is a nuisance; a cancer screen that misses '
        'tumors is a tragedy. The same raw predictions can be excellent for one '
        'application and unacceptable for another, because the costs of different '
        'errors differ. This document builds the vocabulary — confusion matrices, '
        'precision, recall, F1, ROC curves — that lets you say precisely what "good" '
        'means for your problem, instead of hiding behind a single accuracy number.'))
    s.extend(takeaway('Chapter 1 - Key Takeaways', [
        'Evaluation measures future performance; training metrics measure memorization.',
        'Always evaluate on data the model has never seen during training or tuning.',
        '"Good" is problem-dependent: error costs differ across applications.',
        'One number never suffices — this document builds the full metric toolkit.',
    ]))

    s.append(h1('Chapter 2: The Confusion Matrix'))
    s.append(p(
        'For binary classification, every prediction falls into one of four buckets. '
        'The confusion matrix organizes them by actual class (rows) versus predicted '
        'class (columns). By convention we call the class of interest "positive" — '
        'the disease present, the email is spam, the transaction is fraud — even '
        'though "positive" here carries no value judgment.'))
    s.extend(datatable(
        ['', 'Predicted: Positive', 'Predicted: Negative'],
        [['Actual: Positive', 'True Positives (TP): correctly flagged', 'False Negatives (FN): missed cases'],
         ['Actual: Negative', 'False Positives (FP): false alarms', 'True Negatives (TN): correctly cleared']],
        caption='Table 1: The confusion matrix. Rows are reality, columns are the model\'s claims.'))
    s.append(h2('A worked example: the spam filter'))
    s.append(p(
        'A spam filter processes 200 emails. Reality: 50 are spam, 150 are legitimate. '
        'The filter flags 60 emails as spam. Of those 60, 40 truly are spam (TP = 40) '
        'and 20 are legitimate mail wrongly flagged (FP = 20). Of the 140 it lets '
        'through, 130 are genuinely fine (TN = 130) but 10 spam messages slip into the '
        'inbox (FN = 10). Check the arithmetic: TP + FN = 40 + 10 = 50 actual spam; '
        'FP + TN = 20 + 130 = 150 actual legitimate; total 200.'))
    s.append(p(
        'Accuracy is (TP + TN) / total = (40 + 130) / 200 = 0.85, or 85 percent. That '
        'single number hides two very different failures: 20 false alarms annoying '
        'users, and 10 missed spam. Which failure matters more? For spam, false alarms '
        'are worse — missing an important email hurts more than seeing an ad for '
        'watches. For cancer screening the priorities flip entirely. The confusion '
        'matrix forces you to look at the error types separately instead of averaging '
        'them away.'))
    s.extend(takeaway('Chapter 2 - Key Takeaways', [
        'The confusion matrix splits predictions into TP, FP, TN, FN: reality vs. the model\'s claims.',
        '"Positive" means the class of interest, not something desirable.',
        'Accuracy = (TP + TN) / total; it averages over error types that may matter unequally.',
        'Always inspect the four cells before trusting any summary metric.',
    ]))

    s.append(h1('Chapter 3: Precision and Recall'))
    s.append(p(
        'Precision and recall are the two fundamental lenses on the confusion matrix, '
        'each answering a different question about the positive predictions and the '
        'actual positives.'))
    s.append(h2('Definitions'))
    s.append(p(
        'Precision asks: of everything the model flagged as positive, how many were '
        'truly positive? Precision = TP / (TP + FP). It measures the trustworthiness '
        'of a positive prediction — the cost of false alarms. Recall asks: of all the '
        'actual positives out there, how many did the model catch? Recall = TP / '
        '(TP + FN). It measures coverage — the cost of missed cases. (Recall is also '
        'called sensitivity or the true positive rate.)'))
    s.append(h2('Back to the spam filter'))
    s.append(p(
        'Recall our numbers: TP = 40, FP = 20, FN = 10. Precision = 40 / (40 + 20) = '
        '40/60 = 0.667: when the filter cries spam, it is right two-thirds of the '
        'time. Recall = 40 / (40 + 10) = 40/50 = 0.80: it catches 80 percent of all '
        'real spam. Suppose we make the filter more aggressive so it flags 80 emails: '
        'TP rises to 46, FP jumps to 34, FN drops to 4. New precision = 46/80 = 0.575 '
        '(worse — more false alarms), new recall = 46/50 = 0.92 (better — fewer '
        'misses). Aggressiveness trades precision for recall; conservatism does the '
        'reverse. You cannot maximize both by threshold-tuning alone.'))
    s.append(h2('When each matters'))
    s.append(bullets([
        '<b>Precision matters</b> when false alarms are expensive: spam filtering (losing real email), '
        'legal document review (lawyers must read every flagged page), recommendation ("you may like" '
        'suggestions that erode trust when wrong).',
        '<b>Recall matters</b> when misses are catastrophic: cancer screening, fraud detection, '
        'manufacturing defect detection, search-and-rescue image analysis. Missing one case can dwarf '
        'the cost of a hundred false alarms.',
        '<b>Often both matter</b>, which is why we need a combined metric — the subject of the next chapter.',
    ]))
    s.append(p(
        'A useful habit: before looking at any metric, write down which error your '
        'application fears more. That single sentence determines whether you optimize '
        'precision, recall, or a balance — and it prevents the common failure of '
        'tuning a threshold to maximize accuracy while the business bleeds from the '
        'error type accuracy ignores.'))
    s.extend(takeaway('Chapter 3 - Key Takeaways', [
        'Precision = TP/(TP+FP): trust in positive predictions; punishes false alarms.',
        'Recall = TP/(TP+FN): fraction of real positives caught; punishes misses.',
        'Threshold tuning trades one against the other — you cannot maximize both at once.',
        'Decide which error your application fears before choosing what to optimize.',
    ]))
    return s

def story_eval_ch4_7():
    s = []
    s.append(h1('Chapter 4: The F1 Score'))
    s.append(p(
        'When both precision and recall matter, reporting two numbers is honest but '
        'awkward for comparing models. The F1 score combines them into one number — '
        'but not with a simple average. It uses the harmonic mean: '
        'F1 = 2 * (precision * recall) / (precision + recall). The harmonic mean has a '
        'deliberate property: it punishes imbalance. A model must do well on both to '
        'score well overall.'))
    s.append(h2('Why the harmonic mean, not the ordinary average?'))
    s.append(p(
        'Worked comparison. Model A: precision 0.90, recall 0.10 — it is extremely '
        'cautious, almost never flagging, but nearly always right when it does. '
        'Ordinary average: (0.90 + 0.10) / 2 = 0.50, which looks respectable. '
        'Harmonic mean: 2 * 0.90 * 0.10 / (0.90 + 0.10) = 0.18 / 1.0 = 0.18 — a damning '
        'score that reflects the model\'s uselessness at finding positives. Model B, '
        'balanced: precision 0.667, recall 0.80 (our spam filter). F1 = '
        '2 * 0.667 * 0.80 / (0.667 + 0.80) = 1.067 / 1.467 = 0.727. The harmonic mean '
        'is always closer to the smaller of the two values, which is exactly the '
        'behavior you want when a model that ignores one metric should not be '
        'rewarded.'))
    s.append(p(
        'F1 is the right single number when false alarms and misses both carry real '
        'cost and you need to rank models: information retrieval, named-entity '
        'recognition, defect detection. Its limitation is symmetry of concern — if '
        'your application genuinely cares about recall ten times more than precision '
        '(cancer screening), F1\'s equal weighting misleads, and you should use the '
        'weighted F-beta score or optimize recall at a fixed precision floor instead.'))
    s.extend(takeaway('Chapter 4 - Key Takeaways', [
        'F1 = 2PR/(P+R), the harmonic mean of precision and recall.',
        'The harmonic mean punishes lopsided models; it hugs the weaker of the two metrics.',
        'Use F1 when both error types matter and you need one number to rank models.',
        'For asymmetric costs, use F-beta or constrain one metric and optimize the other.',
    ]))

    s.append(h1('Chapter 5: ROC Curves and AUC'))
    s.append(p(
        'Precision, recall, and F1 all depend on a chosen decision threshold. The ROC '
        '(receiver operating characteristic) curve removes the threshold from the '
        'picture: it shows the tradeoff across every possible threshold at once. For '
        'each threshold, compute the true positive rate TPR = TP / (TP + FN) — which '
        'is just recall — and the false positive rate FPR = FP / (FP + TN): the '
        'fraction of actual negatives wrongly flagged. Plot TPR against FPR as the '
        'threshold sweeps from strict to lax.'))
    s.append(h2('Reading the curve'))
    s.append(p(
        'A perfect classifier hugs the top-left corner: it achieves TPR = 1 with '
        'FPR = 0. A random classifier — coin flip — traces the diagonal, catching '
        'positives and negatives at equal rates. A real model bows above the diagonal; '
        'the more it bows toward the corner, the better. The curve also exposes '
        'operating points: the threshold where the curve is steepest buys the most '
        'recall per false alarm, which is often where you want to operate.'))
    s.append(h2('AUC: area under the curve'))
    s.append(p(
        'AUC compresses the whole curve into one number between 0 and 1. It has a '
        'beautiful probabilistic meaning: AUC is the probability that the model ranks '
        'a randomly chosen positive higher than a randomly chosen negative. AUC 0.5 '
        'is random guessing; 1.0 is perfect separation. In practice: 0.9+ is '
        'excellent, 0.8-0.9 good, 0.7-0.8 fair, below 0.7 weak. AUC\'s great strength '
        'is threshold-independence — it measures ranking quality, not one operating '
        'point — which makes it ideal for comparing models before you have chosen a '
        'threshold.'))
    s.append(p(
        'The caveat: AUC can flatter models on highly imbalanced data. With 1 fraud '
        'in 10,000 transactions, a model can achieve AUC 0.95 while its precision at '
        'any usable threshold is miserable — because FPR\'s denominator (all '
        'negatives) is enormous, so even thousands of false alarms barely move the '
        'curve. For heavy imbalance, prefer the precision-recall curve and its area '
        '(average precision), which keeps the spotlight on the rare class you '
        'actually care about.'))
    s.extend(takeaway('Chapter 5 - Key Takeaways', [
        'The ROC curve plots TPR vs FPR across all thresholds; top-left is perfect.',
        'AUC = P(model ranks a random positive above a random negative); 0.5 is chance.',
        'AUC compares ranking quality without committing to a threshold.',
        'On heavily imbalanced data, AUC can mislead — use precision-recall curves instead.',
    ]))

    s.append(h1('Chapter 6: Beyond Accuracy - The Class Imbalance Trap'))
    s.append(p(
        'Accuracy fails most dramatically exactly when you need evaluation most: rare '
        'events. Fraud, disease, defects, and churn are all rare — and in every case '
        'the naive "predict the majority class" model scores high accuracy while '
        'being completely useless. This is the accuracy paradox, and recognizing it '
        'is a rite of passage.'))
    s.append(h2('The paradox, quantified'))
    s.append(p(
        'A factory produces 10,000 parts; 100 are defective (1 percent). Model X '
        'predicts "good" for everything: accuracy 99 percent, recall on defects 0 — it '
        'catches nothing. Model Y catches 80 defects (TP = 80, FN = 20) with 200 false '
        'alarms (FP = 200, TN = 9,700): accuracy = (80 + 9,700) / 10,000 = 97.8 '
        'percent — lower than the useless model! But precision = 80/280 = 0.286 and '
        'recall = 80/100 = 0.80, F1 = 0.42. Every metric except accuracy correctly '
        'prefers Model Y. If you had optimized accuracy, you would have shipped the '
        'model that catches zero defects.'))
    s.append(h2('Coping strategies'))
    s.append(bullets([
        '<b>Right metric first:</b> optimize F1, average precision, or recall-at-fixed-precision — never raw accuracy.',
        '<b>Resampling:</b> oversample the minority class (or synthesize with SMOTE) or undersample the majority for training; '
        'always evaluate on the natural distribution.',
        '<b>Class weights:</b> penalize minority-class errors more heavily in the loss function.',
        '<b>Threshold tuning:</b> lower the decision threshold to favor recall, then check precision at that operating point.',
        '<b>Anomaly framing:</b> for extreme rarity, treat the problem as anomaly detection rather than classification.',
    ]))
    s.extend(takeaway('Chapter 6 - Key Takeaways', [
        'On imbalanced data, a useless majority-class model can beat a useful one on accuracy.',
        'Never optimize accuracy when classes are imbalanced; use F1, PR-AUC, or constrained recall.',
        'Fix imbalance with resampling, class weights, or threshold tuning — evaluated on natural data.',
        'Extreme rarity may call for anomaly detection instead of classification.',
    ]))

    s.append(h1('Chapter 7: Model Selection - Comparing Models Fairly'))
    s.append(p(
        'Model selection is the meta-task: given several candidate models, pick the '
        'one to deploy. The principles are the same as single-model evaluation, with '
        'extra traps around fairness and leakage.'))
    s.append(h2('The validation protocol'))
    s.append(p(
        'Split data into train, validation, and test — or use cross-validation when '
        'data is scarce. Train each candidate on the training portion, rank them on '
        'the validation portion using the metric matched to your problem (Chapter 1\'s '
        'advice: write down which error you fear first), tune the winner\'s '
        'hyperparameters on validation, and report final performance exactly once on '
        'the test set. The test set is a vault: every peek leaks information and '
        'inflates the estimate. Teams that "test-set hill-climb" — repeatedly tuning '
        'until the test score looks good — are overfitting to the test set, and their '
        'deployed performance disappoints.'))
    s.append(h2('Comparing fairly'))
    s.append(bullets([
        '<b>Same data, same metric:</b> every candidate sees identical train/validation splits and is ranked by the same metric.',
        '<b>Account for variance:</b> with cross-validation, compare mean scores with their spread; a 0.5-point win inside '
        'the noise is not a win. Paired tests across folds add rigor.',
        '<b>Match the operating point:</b> compare models at the threshold you will actually deploy, or compare '
        'threshold-free metrics like AUC — not one model\'s best threshold against another\'s default.',
        '<b>Consider cost:</b> a 1-point F1 gain that triples inference latency or training cost may not survive contact '
        'with production. Evaluation includes the budget.',
        '<b>Simplicity wins ties:</b> among statistically indistinguishable models, ship the simpler one — it is easier '
        'to debug, explain, and maintain.',
    ]))
    s.append(p(
        'A closing thought that ties this document together: evaluation is where '
        'machine learning meets accountability. The confusion matrix, precision and '
        'recall, F1, ROC curves, and disciplined validation are not academic '
        'ornaments — they are the instruments that let you promise, with evidence, '
        'that your model will behave. Choose the metric that matches your error '
        'costs, measure it honestly on unseen data, and let the numbers — not the '
        'narrative — pick the model.'))
    s.extend(takeaway('Chapter 7 - Key Takeaways', [
        'Rank candidates on validation with the metric matched to your error costs; test once at the end.',
        'Compare on identical splits and metrics; respect variance — noise is not a win.',
        'Compare at deployable operating points or with threshold-free metrics like AUC.',
        'Among near-ties, ship the simpler, cheaper model.',
    ]))
    return s

# ------------------------------------------------------------ main --------
def main():
    jobs = [
        ('Introduction_to_Machine_Learning.pdf',
         'Introduction to Machine Learning',
         'A university-style primer: paradigms, regression, classification, '
         'overfitting, and honest evaluation.',
         story_ml_intro() + story_ml_intro_ch3_6() + story_ml_intro_ch7()),
        ('Neural_Networks_and_Deep_Learning.pdf',
         'Neural Networks and Deep Learning',
         'From the artificial neuron to CNNs: activations, backpropagation, '
         'optimization, and training craft.',
         story_nn_deep() + story_nn_deep_ch5_7() + story_nn_deep_ch8()),
        ('Machine_Learning_Evaluation.pdf',
         'Machine Learning Evaluation',
         'Measuring what matters: confusion matrices, precision, recall, F1, '
         'ROC curves, and fair model selection.',
         story_eval() + story_eval_ch4_7() + story_eval_ch8()),
    ]
    for filename, doctitle, subtitle, story in jobs:
        path = build_pdf(filename, doctitle, subtitle, story)
        print('wrote', path)


# --------------------------------------- PDF 1 extra: full workflow -------
def story_ml_intro_ch7():
    s = []
    s.append(h1('Chapter 7: Putting It Together - A Complete Workflow'))
    s.append(p(
        'Theory becomes skill through a full pass over a real problem. Imagine a '
        'bike-share operator asking: "How many bikes will be rented tomorrow?" The '
        'target is a number, so this is regression. Candidate features: day of week, '
        'temperature forecast, whether it is a holiday, and rentals on the same date '
        'last year.'))
    s.append(h2('Step 1: frame and split'))
    s.append(p(
        'Before touching a model, write down the performance measure: the operator '
        'plans staffing from the forecast, so large errors hurt disproportionately — '
        'mean squared error on a held-out test set is a defensible choice. Split two '
        'years of daily data into train (first 18 months), validation (next 3), and '
        'test (final 3). The chronological split matters: shuffling would let the '
        'model peek at the future, a subtle form of leakage.'))
    s.append(h2('Step 2: baseline first'))
    s.append(p(
        'Always build the dumbest reasonable model first. Here: predict tomorrow\'s '
        'rentals as the average of the same weekday over the past month. Suppose it '
        'scores MSE 41,000 (root MSE about 202 bikes) on validation. This number is '
        'your hurdle — any fancier model must beat it to earn its complexity. Skip '
        'the baseline and you will never know whether your gradient-boosted ensemble '
        'is brilliant or merely complicated.'))
    s.append(h2('Step 3: model, tune, diagnose'))
    s.append(p(
        'Fit linear regression on the features: validation MSE drops to 28,000. Add '
        'regularization and tune its strength on the validation set: 24,500. Try a '
        'random forest: 21,000 — but training MSE is 9,000, a wide gap that smells of '
        'overfitting (Chapter 5). Constrain tree depth and the gap narrows: training '
        '12,000, validation 19,800. The learning curves — error plotted against '
        'training-set size — show validation error still falling as data grows, which '
        'suggests collecting another season of data would help more than further '
        'tuning.'))
    s.append(h2('Step 4: report once, honestly'))
    s.append(p(
        'Evaluate the chosen model exactly once on the test set: MSE 20,400 (root MSE '
        'about 143 bikes versus the baseline\'s 202 — a 29 percent improvement). '
        'Report the baseline alongside, describe the split, and note the residual '
        'analysis: errors spike on rainy holidays, a segment worth modeling '
        'explicitly next quarter. That loop — frame, baseline, tune, diagnose, '
        'report — is the entire discipline of applied machine learning in miniature, '
        'and every chapter of this document was a piece of it.'))
    s.extend(takeaway('Chapter 7 - Key Takeaways', [
        'Frame the problem first: target type decides regression vs classification; error costs decide the metric.',
        'Split chronologically when time matters; shuffling time series leaks the future.',
        'Build a dumb baseline before anything fancy — complexity must earn its keep.',
        'Diagnose with learning curves and residual analysis, not just a single score.',
        'Report the final number once, on untouched test data, alongside the baseline.',
    ]))
    return s


# --------------------------------- PDF 2 extra: loss functions ------------
def story_nn_deep_ch8():
    s = []
    s.append(h1('Chapter 8: Loss Functions - What the Network Actually Optimizes'))
    s.append(p(
        'Backpropagation needs a differentiable loss — a smooth number that says how '
        'wrong the network is and provides gradients. Accuracy cannot serve: it is a '
        'step function (a prediction flips from wrong to right discontinuously), so '
        'its gradient is zero almost everywhere and undefined at the jumps. Loss '
        'functions are smooth surrogates that correlate with what we care about while '
        'remaining optimizable. Choosing the right one is as important as choosing '
        'the architecture.'))
    s.append(h2('Mean squared error for regression'))
    s.append(p(
        'For predicting numbers, mean squared error (MSE) is standard: average the '
        'squared differences between predictions and targets. Its gradient is '
        'proportional to the error itself, so large mistakes generate strong '
        'correction signals — the same property that made it the cost function for '
        'linear regression in the introductory document. Pair it with a linear '
        '(activation-free) output layer so predictions are unbounded.'))
    s.append(h2('Cross-entropy for classification'))
    s.append(p(
        'For classification, the standard is cross-entropy, which measures how far '
        'the predicted probability distribution is from the truth. Binary case: if '
        'the true label is 1 and the network outputs probability p, the loss is '
        '-log(p); if the label is 0, the loss is -log(1-p). Confident and right is '
        'cheap; confident and wrong is catastrophically expensive. Worked example: '
        'true label 1. Output p = 0.9 gives loss -log(0.9) = 0.105. Output p = 0.6 '
        'gives 0.511. Output p = 0.1 — confident but wrong — gives 2.303. The loss '
        'grows steeply as confidence in the wrong answer rises, which is why '
        'cross-entropy trains classifiers to be calibrated, not just decisive.'))
    s.append(p(
        'For multi-class problems the same idea extends: with softmax outputs and a '
        'one-hot target, categorical cross-entropy is -log of the probability '
        'assigned to the correct class. Notice the elegant pairing from Chapter 2: '
        'softmax outputs plus cross-entropy loss is the canonical combination, and '
        'its gradient has a beautifully simple form (predicted minus target), which '
        'keeps optimization well-behaved.'))
    s.append(h2('Matching loss to task'))
    s.extend(datatable(
        ['Task', 'Output activation', 'Loss function', 'Why'],
        [['Regression', 'Linear (none)', 'Mean squared error',
          'Penalizes large errors quadratically; smooth gradients'],
         ['Binary classification', 'Sigmoid', 'Binary cross-entropy',
          'Punishes confident wrong answers steeply'],
         ['Multi-class classification', 'Softmax', 'Categorical cross-entropy',
          'Simple predicted-minus-target gradient']],
        caption='Table 1: Canonical output/loss pairings. Mismatching them is a common beginner bug.'))
    s.append(p(
        'A final connection to evaluation: the loss is what you optimize, but it is '
        'rarely what you report. You train with cross-entropy and report precision, '
        'recall, or F1 — the metrics from the evaluation document — because the '
        'business cares about error types, not about the surrogate that made '
        'gradients flow. Keep the two roles distinct: loss for training, metrics for '
        'judgment.'))
    s.extend(takeaway('Chapter 8 - Key Takeaways', [
        'Accuracy is not differentiable, so it cannot be a loss; use smooth surrogates for training.',
        'MSE for regression with linear outputs; cross-entropy for classification with sigmoid/softmax.',
        'Cross-entropy punishes confident wrong answers steeply, encouraging calibrated probabilities.',
        'Train on the loss, but judge and report with task metrics like precision, recall, and F1.',
    ]))
    return s


# --------------------------- PDF 3 extra: calibration + mistakes ----------
def story_eval_ch8():
    s = []
    s.append(h1('Chapter 8: Calibration - When Probabilities Must Mean What They Say'))
    s.append(p(
        'Precision, recall, and ROC curves judge rankings and decisions. But many '
        'systems consume raw probabilities: a loan model\'s 0.8 default probability '
        'sets the interest rate; a weather model\'s 0.7 rain probability decides '
        'whether the game is cancelled. Calibration asks whether those numbers mean '
        'what they claim: among all cases where the model said 0.8, did about 80 '
        'percent actually turn out positive? A model can rank perfectly (AUC 1.0) '
        'while being wildly miscalibrated — outputting 0.51 for every positive and '
        '0.49 for every negative ranks flawlessly and means nothing.'))
    s.append(h2('Measuring calibration'))
    s.append(p(
        'The reliability diagram bins predictions by confidence (0.0-0.1, 0.1-0.2, '
        'and so on) and plots the actual positive rate in each bin against the bin\'s '
        'average predicted probability. Perfect calibration is the diagonal. A curve '
        'below the diagonal means overconfidence — the classic deep-network failure, '
        'where models output 0.99 on guesses barely better than chance. The Brier '
        'score (mean squared error between predicted probabilities and 0/1 outcomes) '
        'and expected calibration error summarize miscalibration in one number.'))
    s.append(h2('Fixing it'))
    s.append(p(
        'If ranking is good but calibration is off, post-hoc fixes apply without '
        'retraining: Platt scaling fits a logistic curve mapping raw scores to '
        'calibrated probabilities on a held-out set; isotonic regression fits a more '
        'flexible monotonic mapping when data is plentiful; temperature scaling — a '
        'single-parameter variant — is the modern default for neural networks. '
        'Calibrate on validation data, verify on test data, and re-check after any '
        'distribution shift, because calibration decays as the world changes.'))
    s.extend(takeaway('Calibration - Key Takeaways', [
        'Calibration means predicted probabilities match observed frequencies; ranking quality does not imply it.',
        'Diagnose with reliability diagrams; summarize with Brier score or expected calibration error.',
        'Fix with Platt scaling, isotonic regression, or temperature scaling on held-out data.',
        'Recalibrate after distribution shift — calibration decays as the world changes.',
    ]))

    s.append(h1('Chapter 9: Common Evaluation Mistakes'))
    s.append(p(
        'Most evaluation failures are not mathematical — they are procedural. A '
        'checklist of the classics:'))
    s.extend(datatable(
        ['Mistake', 'What happens', 'The fix'],
        [['Training on the test set',
          'Memorization scores as learning; deployed performance collapses',
          'Lock the test set away until final reporting'],
         ['Preprocessing before splitting',
          'Imputation/scaling statistics leak test information into training',
          'Fit all preprocessing on train only; apply to the rest'],
         ['Ignoring time order',
          'Random splits let the model learn from the future',
          'Split chronologically for time-dependent data'],
         ['Tuning on the test set',
          'Repeated tweaks overfit the test set itself',
          'Tune on validation; touch test exactly once'],
         ['Accuracy on imbalanced data',
          'Useless majority-class models look excellent',
          'Use precision, recall, F1, or PR-AUC'],
         ['Single lucky split',
          'One favorable partition inflates the reported score',
          'Use cross-validation and report the spread'],
         ['Leaking the target',
          'A feature contains the answer (e.g., "cancellation reason" predicting churn)',
          'Audit features for post-outcome information']],
        caption='Table 2: The evaluation hall of shame. Every row has embarrassed a real team.'))
    s.append(p(
        'Notice how many of these are about information flow — what the model was '
        'allowed to see, and when. Rigorous evaluation is, at bottom, an exercise in '
        'epistemic hygiene: ensuring the number you report measures what you claim '
        'it measures. Get the procedure right and the metrics take care of '
        'themselves; get it wrong and no metric can save you.'))
    s.extend(takeaway('Chapter 9 - Key Takeaways', [
        'Most evaluation failures are procedural (leakage, bad splits), not mathematical.',
        'Fit preprocessing on training data only; split chronologically when time matters.',
        'Audit features for target leakage — post-outcome information is the silent killer.',
        'Evaluation is epistemic hygiene: the number must measure what you claim it measures.',
    ]))
    return s

if __name__ == "__main__":
    main()
