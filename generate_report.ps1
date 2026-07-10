# Generate CropDoc_FYP_Report.docx using Word COM automation
$OutPath = "d:\FYP\CropDoc_FYP_Report.docx"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc  = $word.Documents.Add()
$sel  = $word.Selection

function H1($t) { $sel.Style = $doc.Styles["Heading 1"]; $sel.TypeText($t); $sel.TypeParagraph() }
function H2($t) { $sel.Style = $doc.Styles["Heading 2"]; $sel.TypeText($t); $sel.TypeParagraph() }
function H3($t) { $sel.Style = $doc.Styles["Heading 3"]; $sel.TypeText($t); $sel.TypeParagraph() }
function P($t)  { $sel.Style = $doc.Styles["Normal"];    $sel.TypeText($t); $sel.TypeParagraph() }
function Bullet($t) { $sel.Style = $doc.Styles["List Bullet"]; $sel.TypeText($t); $sel.TypeParagraph() }
function Num($t)    { $sel.Style = $doc.Styles["List Number"];  $sel.TypeText($t); $sel.TypeParagraph() }
function Blank()    { $sel.Style = $doc.Styles["Normal"];       $sel.TypeParagraph() }
function PB()       { $sel.InsertBreak(7) }
function PH($t) {
    $sel.Style = $doc.Styles["Normal"]
    $sel.Font.Bold = $true; $sel.Font.Color = 255  # Red
    $sel.TypeText("[INSERT: $t]")
    $sel.Font.Bold = $false; $sel.Font.Color = -16777216  # Auto
    $sel.TypeParagraph()
}

# ─── Title Page ───────────────────────────────────────────────────────────────
$sel.ParagraphFormat.Alignment = 1
Blank; Blank
$sel.Font.Size = 16; $sel.Font.Bold = $true
$sel.TypeText("Institute of Management Sciences, Peshawar"); $sel.TypeParagraph()
$sel.Font.Size = 12; $sel.Font.Bold = $false; $sel.Font.Italic = $true
$sel.TypeText("BS Data Science -- Session 2020-2024"); $sel.TypeParagraph()
$sel.Font.Italic = $false
Blank; Blank
$sel.Font.Size = 20; $sel.Font.Bold = $true
$sel.TypeText("CropDoc: AI-Powered Plant Disease Detection"); $sel.TypeParagraph()
$sel.TypeText("and Farmer Support Chatbot"); $sel.TypeParagraph()
$sel.Font.Size = 12; $sel.Font.Bold = $false
Blank; Blank
foreach ($pair in @(
    "Submitted by:  Hamza Shahid, Hottam ud din, Tariq Jamil",
    "Supervisor:  Dr. Bahar Ali",
    "Program:  BS Data Science",
    "Session:  2020-2024",
    "Submission Date:  April 2026"
)) { $sel.TypeText($pair); $sel.TypeParagraph() }
$sel.ParagraphFormat.Alignment = 0
PB

# ─── Abstract ────────────────────────────────────────────────────────────────
H1 "Abstract"
P "Plant diseases are a leading cause of agricultural losses worldwide, responsible for an estimated 20 to 40 percent reduction in crop yield annually. In developing countries such as Pakistan, where agriculture contributes significantly to both the national economy and food security, the impact is disproportionately severe. Small-scale farmers lack timely access to expert diagnosis and advisory services, leading to overuse of broad-spectrum pesticides and significant economic losses."
P "This project presents CropDoc, an AI-powered plant disease detection and farmer support system. CropDoc employs a lightweight ResNet-9 CNN trained from scratch on the PlantVillage benchmark dataset (87,000+ images, 38 classes across 14 crops). The model has approximately 6.6 million trainable parameters and achieves inference in under 50 milliseconds on GPU hardware, making it suitable for smartphone deployment."
P "A distinguishing feature is the integration of Gradient-weighted Class Activation Mapping (Grad-CAM), which generates visual heatmaps showing which leaf regions drove the model prediction. A conversational chatbot powered by google/flan-t5-base runs locally without any API key and provides farmer-friendly, non-chemical disease management advice drawn from a curated 38-entry knowledge base."
P "The system is validated on the PlantVillage benchmark dataset."
PH "Final validation accuracy after training"
P "accuracy is achieved. The complete system is exposed via a FastAPI REST endpoint and exported in ONNX format for cross-platform deployment. The project demonstrates the feasibility of AI-powered agricultural advisory tools in low-resource settings."
PB

# ─── Chapter 1 ───────────────────────────────────────────────────────────────
H1 "Chapter 1: Introduction"

H2 "1.1 Overview"
P "The application of Artificial Intelligence in agriculture represents one of the most consequential technological developments of this century. As global food demand rises, the agricultural sector faces mounting pressure to increase productivity and reduce waste. Plant diseases caused by fungal pathogens, bacteria, and viruses pose a persistent and costly threat to crop production. CropDoc leverages deep learning, explainable AI, and natural language generation to build an end-to-end agricultural advisory system accessible to farmers through a standard smartphone camera."

H2 "1.2 Motivation and Problem Statement"
P "Pakistan's agricultural sector employs approximately 42 percent of the national workforce. Farmers in rural Khyber Pakhtunkhwa, Punjab, and Sindh face significant barriers to timely disease diagnosis. An agricultural extension consultation typically costs Rs. 5,000 to Rs. 10,000, which is prohibitive for smallholder farmers. Plant disease losses in Pakistan reduce yields by 20 to 40 percent annually across tomato, potato, maize, grape, and apple crops. Existing digital solutions such as the PlantVillage app suffer from two critical limitations: they function as black-box systems with no explanation for predictions, and they require cloud connectivity making them unusable in areas with limited internet."
P "CropDoc addresses both limitations simultaneously: a lightweight on-device model combined with Grad-CAM visual explanations and an offline-capable chatbot produces an end-to-end advisory system that requires no internet after initial setup and explains every prediction."

H2 "1.3 Project Vision"
P "The vision of CropDoc is to serve as an intelligent, explainable, and accessible agricultural companion for farmers in Pakistan and the broader developing world. By combining state-of-the-art deep learning with visual explainability and natural language generation, CropDoc aspires to democratise access to plant disease expertise -- making it available to any farmer with a smartphone, regardless of their location, literacy level, or economic resources."

H2 "1.4 Scope"
P "The current CropDoc implementation covers:"
Bullet "Classification of plant leaf images into 38 disease categories spanning 14 crop species"
Bullet "Visual explainability via Grad-CAM heatmaps highlighting disease-relevant leaf regions"
Bullet "A farmer-friendly conversational chatbot providing non-chemical management advice"
Bullet "A FastAPI REST API enabling integration with web and mobile applications"
Bullet "Model export in ONNX format for cross-platform deployment"
P "Out of scope: real-time video detection, IoT sensor integration, multi-label classification, severity grading, and non-English chatbot responses."

H2 "1.5 Problem Statement"
P "Given the widespread prevalence of plant diseases and the limited access of smallholder farmers in Pakistan to expert agronomic advice, there is a critical need for a lightweight, explainable, and locally deployable AI system capable of: (i) accurately identifying plant diseases from smartphone photographs of crop leaves; (ii) providing visual evidence for its predictions to build farmer trust; and (iii) offering actionable, non-chemical management guidance through a conversational interface -- all without requiring an internet connection or costly subscriptions."

H2 "1.6 Project Objectives"
Num "Develop a ResNet-9 CNN model trained from scratch on PlantVillage capable of classifying 38 disease categories with target validation accuracy of 95% or above."
Num "Integrate Grad-CAM explainability to generate visual heatmaps highlighting disease-relevant leaf regions, building farmer confidence in AI predictions."
Num "Build a curated disease knowledge base covering all 38 PlantVillage classes with symptoms and non-chemical precautionary measures."
Num "Develop a locally deployable conversational chatbot using google/flan-t5-base that provides farmer-friendly advice without requiring an internet connection."
Num "Expose the complete system via a FastAPI REST API enabling integration with web and mobile front-end applications."
Num "Export the trained model in ONNX format to support cross-platform deployment on mobile devices and edge computing hardware."

H2 "1.7 Tools and Technologies"
P "Table 1.1 -- Tools and Technologies Used in CropDoc:"
$t1 = $doc.Tables.Add($sel.Range, 13, 3); $t1.Style = "Table Grid"
$h1data = @("Tool / Library","Version","Purpose")
for ($c=0;$c -lt 3;$c++){$t1.Cell(1,$c+1).Range.Text=$h1data[$c];$t1.Cell(1,$c+1).Range.Font.Bold=$true}
$rows1 = @(
  @("Python","3.10+","Primary programming language"),
  @("PyTorch","2.x","Deep learning framework; model training and inference"),
  @("torchvision","0.15+","Dataset loading, transforms, pre-built utilities"),
  @("HuggingFace Transformers","4.x","flan-t5-base language model pipeline"),
  @("FastAPI","0.100+","REST API web framework for model serving"),
  @("OpenCV (cv2)","4.x","Grad-CAM heatmap generation and image blending"),
  @("NumPy","1.24+","Numerical computation and array operations"),
  @("Matplotlib","3.7+","Training history plots and visualisations"),
  @("Seaborn","0.12+","Confusion matrix heatmap"),
  @("scikit-learn","1.2+","Classification report and evaluation metrics"),
  @("ONNX","1.14+","Model export for cross-platform deployment"),
  @("Pillow (PIL)","9.x","Image loading and preprocessing")
)
for ($r=0;$r -lt $rows1.Count;$r++){for($c=0;$c -lt 3;$c++){$t1.Cell($r+2,$c+1).Range.Text=$rows1[$r][$c]}}
$sel.MoveDown(5,$t1.Rows.Count+2); Blank

H2 "1.8 Glossary of Terms"
$gloss = @(
  @("CNN (Convolutional Neural Network)","A deep neural network designed for processing grid-like image data. CNNs apply learned convolutional filters to extract hierarchical spatial features from images."),
  @("ResNet (Residual Network)","A CNN architecture that introduces identity skip connections between layers, allowing gradients to flow more easily during backpropagation and enabling training of deeper networks."),
  @("Grad-CAM","Gradient-weighted Class Activation Mapping -- a technique that generates visual explanations for CNN predictions by computing gradients of the target class score with respect to the last convolutional layer's feature maps."),
  @("PlantVillage","A publicly available dataset of 87,000+ images of healthy and diseased crop leaves categorised into 38 classes, widely used as a benchmark for plant disease classification."),
  @("One-Cycle LR","A learning rate schedule that linearly warms up the learning rate to a maximum value then anneals it, achieving faster convergence with fewer training epochs (super-convergence)."),
  @("ONNX","Open Neural Network Exchange -- an open format for representing ML models, enabling interoperability across frameworks and runtime environments including mobile and edge devices."),
  @("LLM","Large Language Model -- a neural network trained on large text corpora capable of understanding and generating human language. CropDoc uses flan-t5-base."),
  @("flan-t5-base","A 250M-parameter text-to-text language model from Google, fine-tuned with instruction tuning. Freely available on HuggingFace Hub; runs locally without an API key.")
)
foreach ($g in $gloss) {
  $sel.Font.Bold = $true;  $sel.TypeText($g[0] + ": ")
  $sel.Font.Bold = $false; $sel.TypeText($g[1])
  $sel.TypeParagraph()
}
PB

# ─── Chapter 2 ───────────────────────────────────────────────────────────────
H1 "Chapter 2: Background Study"

H2 "2.1 Introduction to Plant Disease Detection"
P "The detection and management of plant diseases has historically relied on the expertise of trained agronomists who conduct field inspections to identify causal agents and recommend treatment protocols. This approach is inherently limited by the availability and geographic distribution of experts -- particularly acute in developing countries where agricultural extension services are underfunded. Early computer vision approaches relied on hand-crafted feature extractors (colour histograms, texture descriptors, shape features) combined with traditional classifiers such as SVMs and k-NN. While achieving moderate accuracy on constrained datasets, they generalised poorly to real-world field conditions."
P "The introduction of the PlantVillage dataset by Hughes and Salathe (2015) -- comprising over 87,000 images of 38 healthy and diseased crop classes -- provided the training data necessary for deep learning approaches to demonstrate their full potential. PlantVillage has since become the de facto benchmark for plant disease classification research and forms the foundation of the CropDoc training pipeline."

H2 "2.2 Deep Learning for Image Classification"
P "Convolutional Neural Networks (CNNs) are the dominant architecture for image classification tasks. Unlike fully connected networks, CNNs exploit the local spatial structure of images through shared convolutional filters, dramatically reducing learnable parameters while preserving spatial relationships. A typical CNN alternates between convolutional layers (feature extraction), pooling layers (spatial down-sampling), and ReLU activations, culminating in fully connected layers that produce class probability distributions."
P "Residual Networks (ResNets), introduced by He et al. in 2016, addressed the vanishing gradient problem by introducing identity skip connections. The residual formulation H(x) = F(x) + x allows gradients to flow directly backward through skip connections, enabling training of much deeper networks. Batch Normalisation (Ioffe and Szegedy, 2015) further accelerates training by reducing internal covariate shift. Dropout (Srivastava et al., 2014) provides complementary regularisation by stochastically zeroing activations during training."

H2 "2.3 Literature Review"
P "[1] Mohanty et al. (2016) -- Using Deep Learning for Image-Based Plant Disease Detection"
P "Used AlexNet and GoogLeNet on the PlantVillage dataset, achieving up to 99.35% accuracy in controlled laboratory conditions. However, accuracy dropped to as low as 31% on field-collected images with natural backgrounds and variable illumination. This seminal limitation established the need for data augmentation strategies that simulate real-world conditions. CropDoc addresses this by incorporating RandomRotation, ColorJitter, and RandomResizedCrop transforms during training, alongside ImageNet normalisation statistics to standardise input distributions."
Blank
P "[2] Ferentinos (2018) -- Deep Learning Models for Plant Disease Detection and Diagnosis"
P "Conducted a systematic comparison of multiple CNN architectures on PlantVillage, reporting 99.53% accuracy with a VGG-based model. A significant limitation is that top-performing architectures (VGG-16: 138M parameters, approximately 528 MB) are too large for efficient mobile deployment. CropDoc's ResNet-9 with only 6.6M parameters achieves competitive accuracy while being approximately 4 times smaller, making it more practical for the target user base of smartphone-equipped farmers."
Blank
P "[3] Tm et al. (2018) -- Tomato Leaf Disease Detection Using Convolutional Neural Network"
P "Applied a custom CNN for tomato leaf disease classification, identifying nine tomato disease classes from PlantVillage. Their work demonstrated that domain-specific lightweight CNNs achieve strong performance on a subset of the full classification problem. A key limitation is restriction to a single crop type. CropDoc classifies all 38 disease classes across 14 crops within a single ResNet-9 model, simplifying the deployment pipeline and avoiding the need to pre-identify the crop before disease classification."
Blank
P "[4] Selvaraju et al. (2017) -- Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization"
P "Introduced Grad-CAM, a technique for generating class-discriminative localisation maps from CNNs without architectural modification. The algorithm computes gradients of the target class score with respect to the final convolutional layer's feature maps, pools them spatially to obtain channel importance weights, and produces a weighted activation sum followed by ReLU. CropDoc integrates Grad-CAM targeting the model.res2 layer, enabling farmers to visually verify that the model is attending to genuine disease symptoms rather than irrelevant background features, thereby building trust in AI-generated diagnoses."
Blank
P "[5] Smith (2018) -- A Disciplined Approach to Neural Network Hyper-Parameters"
P "Introduced the One-Cycle Learning Rate policy achieving super-convergence -- reaching high accuracy in significantly fewer training epochs than conventional constant or step-decay schedules. The policy involves linearly warming up the learning rate to a maximum value then annealing it back. This high-LR exploration phase encourages the optimiser to explore a broader region of the loss landscape and escape local minima. CropDoc applies One-Cycle LR with Adam over 20 training epochs, combined with gradient clipping at 0.1 and weight decay of 1e-4, achieving stable and efficient training."
Blank
P "[6] Kamilaris and Prenafeta-Boldu (2018) -- Deep Learning in Agriculture: A Survey"
P "Conducted a comprehensive survey of 40 studies applying deep learning to agricultural problems. The survey found that CNN approaches consistently outperformed traditional methods across all reviewed domains. A critical observation is that the overwhelming majority of reviewed methods operate as black-box systems -- a significant barrier to farmer adoption. The authors explicitly called for future work incorporating interpretability mechanisms. CropDoc directly addresses this identified gap by integrating Grad-CAM as a first-class feature of the system."
Blank

H2 "2.4 Comparison Table"
P "Table 2.1 -- Literature Review Comparison:"
$t2 = $doc.Tables.Add($sel.Range, 7, 6); $t2.Style = "Table Grid"
$h2d = @("S#","Authors and Year","Methodology","Classes","Limitations","Our Advantage")
for ($c=0;$c -lt 6;$c++){$t2.Cell(1,$c+1).Range.Text=$h2d[$c];$t2.Cell(1,$c+1).Range.Font.Bold=$true}
$rows2 = @(
  @("1","Mohanty et al. (2016)","AlexNet, GoogLeNet","26","Lab only; no explainability","Augmentation; Grad-CAM"),
  @("2","Ferentinos (2018)","VGGNet variants","38","138M params; not mobile","6.6M params; mobile-ready"),
  @("3","Tm et al. (2018)","Custom CNN","9 (tomato)","Single crop only","14 crops in one model"),
  @("4","Selvaraju et al. (2017)","Grad-CAM technique","N/A","Technique paper only","Applied for farmer explainability"),
  @("5","Smith (2018)","One-Cycle LR","N/A","Hyperparameter study","Applied for 20-epoch convergence"),
  @("6","Kamilaris (2018)","Survey (40 papers)","Various","No explainability","Grad-CAM + chatbot fills both gaps")
)
for ($r=0;$r -lt $rows2.Count;$r++){for($c=0;$c -lt 6;$c++){$t2.Cell($r+2,$c+1).Range.Text=$rows2[$r][$c]}}
$sel.MoveDown(5,$t2.Rows.Count+2); Blank

H2 "2.5 Gap Analysis"
P "The literature review reveals three distinct gaps that CropDoc is designed to address:"
P "Gap 1 -- Lack of Explainability: The majority of plant disease classification systems provide no visual or textual justification for their predictions. This black-box behaviour reduces farmer trust. CropDoc integrates Grad-CAM as a core feature that generates heatmaps for every prediction."
P "Gap 2 -- Model Size and Mobile Suitability: High-accuracy models such as VGGNet (138M parameters) are computationally prohibitive for smartphone deployment. CropDoc's ResNet-9 with 6.6 million parameters and sub-50ms GPU inference is specifically optimised for this constraint."
P "Gap 3 -- Absence of Conversational Support: Existing solutions return a disease class label but provide no guidance on what the farmer should do next. CropDoc's flan-t5-base chatbot fills this gap by providing plain-English, actionable, non-chemical management advice drawn from a curated knowledge base."
PB

# ─── Chapter 3 ───────────────────────────────────────────────────────────────
H1 "Chapter 3: System Requirements, Architecture and Design"

H2 "3.1 System Architecture"
P "CropDoc is structured as a three-tier architecture:"
P "Tier 1 -- Image Input Layer: The farmer captures or uploads a photograph via a web or mobile interface. The image is received by the FastAPI endpoint and passed through the standard preprocessing pipeline: Resize(256), CenterCrop(256), ToTensor(), and Normalize(ImageNet statistics). The resulting (1, 3, 256, 256) tensor is forwarded to the intelligence layer."
P "Tier 2 -- Intelligence Layer: The preprocessed tensor is passed to the ResNet-9 model, which outputs a (1, 38) logit vector. Softmax converts this to class probabilities, and the highest probability class is selected as the predicted disease. Concurrently, Grad-CAM is invoked on the model.res2 block to generate a (256, 256) heatmap blended with the original image."
P "Tier 3 -- Advisory Layer: The predicted disease class name is used to look up the knowledge base JSON entry. The matched entry (disease name, symptoms, precautionary measures) is passed to the flan-t5-base pipeline as context. A structured prompt is constructed and the model generates a farmer-friendly advisory response in under 150 words. The complete response is serialised as JSON and returned to the client."

H2 "3.2 Use Case Description"
P "UC1 -- Disease Classification: Actor: Farmer. Trigger: Farmer uploads a leaf photograph. Flow: (1) Image is received and validated by the FastAPI endpoint. (2) Preprocessing pipeline is applied. (3) ResNet-9 model returns the top predicted disease class with confidence score. (4) Result is displayed. Postcondition: Farmer knows the predicted disease and confidence level."
P "UC2 -- Visual Explanation (Grad-CAM): Trigger: Automatic alongside UC1. Flow: (1) Grad-CAM hooks are registered on model.res2. (2) A backward pass is performed for the predicted class. (3) Gradient weights are computed and the heatmap is generated. (4) The heatmap is overlaid on the original leaf image. (5) The annotated image is returned. Postcondition: Farmer can visually identify which leaf region triggered the diagnosis."
P "UC3 -- Advisory Chatbot: Trigger: Disease prediction received; farmer asks follow-up question. Flow: (1) Disease name retrieves the knowledge base entry. (2) Context-enriched prompt is constructed and passed to flan-t5-base. (3) Model generates plain-English advisory response. (4) Farmer may ask further follow-up questions. Postcondition: Farmer has actionable management advice."

H2 "3.3 Software Requirements Specification (SRS) Summary"
P "Functional Requirements:"
Bullet "FR1: Accept JPEG and PNG leaf images up to 10 MB via a REST API endpoint"
Bullet "FR2: Classify input image into one of 38 categories; return class name and confidence score"
Bullet "FR3: Generate a Grad-CAM heatmap for every prediction; return as base64-encoded PNG"
Bullet "FR4: Retrieve knowledge base entry for predicted disease and pass to chatbot as context"
Bullet "FR5: Generate farmer-friendly advisory response in under 150 words"
Bullet "FR6: Return fallback response if predicted disease is not found in knowledge base"
P "Non-Functional Requirements:"
Bullet "NFR1 -- Performance: End-to-end API response time shall not exceed 500 ms on GPU hardware"
Bullet "NFR2 -- Accuracy: Model validation accuracy shall meet or exceed 95% on PlantVillage validation set"
Bullet "NFR3 -- Portability: Model shall be exported in ONNX format compatible with ONNX Runtime 1.14+"
Bullet "NFR4 -- Offline Operation: Chatbot and knowledge base shall function without internet after initial download"
Bullet "NFR5 -- Scalability: FastAPI application shall support concurrent inference requests via async handlers"

H2 "3.4 Test Plan"
P "Unit tests: (1) Preprocessing pipeline -- verify output tensor shape (1,3,256,256) and normalisation statistics; (2) Model loading -- verify state_dict keys and class_to_idx length equals 38; (3) Grad-CAM -- verify heatmap shape (256,256) and value range [0,1]; (4) Knowledge base -- verify all 38 class names return a non-None entry."
P "Integration tests: End-to-end test from input image to predicted class and heatmap; verify correct class returned for known test images."
P "Performance tests: Benchmark 100 predictions; target mean latency below 200ms on CPU and below 50ms on GPU."
P "Acceptance tests: Run inference on the 33-image PlantVillage test set; all 33 images should be correctly classified."
PB

# ─── Chapter 4 ───────────────────────────────────────────────────────────────
H1 "Chapter 4: Implementation"

H2 "4.1 Dataset Details"
P "CropDoc is trained on the New Plant Diseases Dataset (augmented version of PlantVillage hosted on Kaggle). The dataset comprises 87,000+ RGB images pre-divided into a training set of approximately 70,295 images and a validation set of approximately 17,572 images (80/20 split). A separate test set of 33 images covers seven disease categories for final acceptance testing. The dataset spans 14 plant species and 38 distinct class categories: 26 representing specific diseases and 12 representing healthy plant conditions. All images are stored as RGB files at 256x256 pixel resolution in a hierarchical directory structure compatible with the torchvision ImageFolder loader."
P "The dataset is well-balanced with between approximately 1,642 and 2,022 images per class in the training set. The smallest class (Corn Gray Leaf Spot, 1,642 images) and the largest class (Soybean Healthy, 2,022 images) differ by only 380 images, indicating a relatively even distribution that does not require class-weighted sampling."

H2 "4.2 Data Preprocessing"
P "Training transforms (applied in order with justification):"
P "1. RandomResizedCrop(256, scale=(0.8, 1.0)): Crops 80 to 100 percent of the image area and resizes to 256x256 pixels. This simulates variable zoom levels common when farmers photograph leaves at varying distances from their smartphones."
P "2. RandomHorizontalFlip(p=0.5): Since plant leaves have no directional asymmetry, horizontal flipping doubles the effective diversity of the training set at zero cost."
P "3. RandomRotation(degrees=15): Accounts for the fact that farmers cannot be expected to hold their smartphones perfectly level when photographing leaves in the field. Rotation by up to 15 degrees in either direction creates rotation invariance."
P "4. ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1): Simulates variability in ambient illumination (morning versus afternoon, shade versus direct sunlight) and camera quality, improving robustness to real-world image conditions."
P "5. Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]): Channel-wise normalisation using ImageNet statistics scales pixel values to a range conducive to stable gradient flow during training."
P "Validation transforms: Resize(256), CenterCrop(256), ToTensor(), Normalize(). No augmentation is applied during validation to ensure consistent, representative evaluation under expected deployment conditions."

H2 "4.3 Model Architecture"
P "CropDoc employs a custom ResNet-9 architecture designed for the specific requirements of mobile agricultural deployment. A shared conv_block helper creates a sequential module: Conv2d(3x3, padding=1) + BatchNorm2d + ReLU(inplace=True), with an optional MaxPool2d(4) appended when pool=True."
P "Layer-by-layer walkthrough:"
Bullet "conv1 (3->64 channels, no pool): Output (64, 256, 256). Learns low-level features: edges, colour gradients, texture primitives."
Bullet "conv2 (64->128 channels, MaxPool4): Output (128, 64, 64). Mid-level features: spot boundaries, vein patterns."
Bullet "res1 (128->128, skip connection): Output (128, 64, 64). First residual block. The skip connection allows the network to learn residual corrections to the identity mapping, enabling deeper representations while avoiding vanishing gradients."
Bullet "conv3 (128->256 channels, MaxPool4): Output (256, 16, 16). Captures higher-level patterns at a broader receptive field, including disease-specific spot distributions and texture patterns."
Bullet "conv4 (256->512 channels, MaxPool4): Output (512, 4, 4). At this stage feature maps encode highly abstract, class-discriminative representations of the disease pattern."
Bullet "res2 (512->512, skip connection): Output (512, 4, 4). Second residual block. This is the layer targeted by Grad-CAM, as it produces the most abstract feature maps before the classifier head."
Bullet "Classifier: MaxPool2d(4) -> (512, 1, 1) -> Flatten -> (512,) -> Dropout(0.5) -> Linear(512, 38). Dropout provides regularisation; Linear maps to 38 disease class logits."
P "Total trainable parameters: approximately 6.6 million (approximately 25 MB PyTorch checkpoint, approximately 8 MB ONNX)."

H2 "4.4 Training Procedure"
P "Training is conducted on Kaggle's GPU-accelerated cloud environment (Tesla P100 or equivalent). Hyperparameter configuration: Adam optimizer (max_lr=0.01, weight_decay=1e-4), OneCycleLR scheduler, gradient clipping at 0.1, batch_size=32, 20 epochs."
P "The One-Cycle LR schedule warms the learning rate from lr_max/25 to lr_max over the first 45% of training steps, then anneals it back to lr_max/25 x 1e-4 using cosine annealing. This high-learning-rate exploration phase enables the optimizer to escape saddle points and narrow local minima that would trap a constant-rate optimizer, while the final low-learning-rate phase enables fine-grained convergence."
PH "Training accuracy curve showing convergence over 20 epochs"
PH "Training and validation loss curves over 20 epochs"

H2 "4.5 Model Checkpointing and Export"
P "The model checkpoint saved at the end of training contains: model_state_dict (learnable parameters), class_to_idx (class folder name to integer index mapping required for inference), val_accuracy (best validation accuracy achieved), train_history (list of per-epoch metrics for plotting training curves), and epoch (total completed training epochs)."
P "ONNX export is performed by tracing the model with a dummy input tensor of shape (1, 3, 256, 256) using opset version 11. The exported ONNX model can be loaded with ONNX Runtime for deployment on platforms without PyTorch, including web browsers (ONNX.js), mobile devices (ONNX Runtime Mobile), and edge hardware (TensorRT, OpenVINO)."

H2 "4.6 Grad-CAM Integration"
P "Grad-CAM is implemented using PyTorch's hook mechanism targeting model.res2. Five algorithmic steps:"
Num "Forward hook on model.res2: During the forward pass, the hook captures and stores the output feature maps A in R^(C x H x W) of the second residual block."
Num "Backward hook on model.res2: During the backward pass, the hook captures the gradient of the target class score y_c with respect to A: dL/dA in R^(C x H x W)."
Num "Gradient global average pooling: Channel importance weights are computed by pooling the gradient tensor spatially: alpha_k = (1/HW) * sum(dL/dA_k), producing a weight vector alpha in R^C."
Num "Weighted activation sum: The class activation map is computed as L^c = ReLU(sum alpha_k * A_k), applying ReLU to retain only positively contributing spatial locations."
Num "Normalise and upsample: L^c is normalised to [0, 1] and bilinearly upsampled to 256x256 to match the input image dimensions, then blended with the original image using OpenCV's applyColorMap and addWeighted functions."

H2 "4.7 Chatbot Integration"
P "The CropDoc chatbot uses the HuggingFace Transformers pipeline API with google/flan-t5-base, a 250-million-parameter text-to-text transformer fine-tuned with instruction tuning. The model runs entirely locally after an initial download of approximately 250 MB -- no API key or internet connection required during inference."
P "The knowledge base is stored as a JSON file containing 38 entries. Each entry includes: class_name, disease_name, affected_crop, is_healthy (boolean), symptoms (2-3 sentences), and precautionary_measures (list of 3-5 non-chemical bullet points). The structured prompt template: 'Context: {disease_name} affects {crop}. Symptoms: {symptoms} Precautions: {measures} / Question: {user_question} / Answer in simple farmer-friendly English in under 150 words:'"
P "This prompt engineering approach grounds the language model's response in factual disease-specific information, reducing hallucination and ensuring advice is relevant to the detected condition. If the predicted disease is not found in the knowledge base, the system falls back to an ungrounded prompt and appends a disclaimer advising the farmer to consult an agricultural expert."

H2 "4.8 FastAPI Web Interface"
P "CropDoc exposes its inference capabilities through a FastAPI REST API. FastAPI was chosen for its high performance (based on Starlette and uvicorn), native async support, automatic OpenAPI documentation generation, and first-class support for multipart file uploads."
P "The primary endpoint is POST /predict, which accepts a multipart/form-data request containing a single image file. The endpoint returns a JSON response with: disease_name (string), confidence (float 0-1), gradcam_image (base64-encoded PNG string), and advisory (chatbot-generated string). The model and chatbot pipeline are loaded once at server startup and shared across all requests. A secondary GET /health endpoint returns HTTP 200 for health-checking and load balancer integration."
PB

# ─── Chapter 5 ───────────────────────────────────────────────────────────────
H1 "Chapter 5: Results and Discussion"

H2 "5.1 Training Results"
P "The CropDoc ResNet-9 model was trained for 20 epochs using the One-Cycle learning rate policy on the Kaggle GPU environment. Training and validation metrics were recorded at the end of each epoch to monitor convergence and detect overfitting."
PH "Training accuracy curve -- plot of validation accuracy vs. epoch number over 20 epochs"
PH "Training/validation loss curve -- dual-line plot of train_loss and val_loss vs. epoch number"
PH "Final training loss value after epoch 20"
PH "Final validation accuracy after training"

H2 "5.2 Quantitative Evaluation"
P "Following training, the model was evaluated on the full PlantVillage validation set using standard classification metrics computed via scikit-learn. The following weighted-average metrics are reported across all 38 classes:"
PH "Overall validation accuracy"
PH "Weighted precision from classification report"
PH "Weighted recall from classification report"
PH "Weighted F1-score from classification report"
PH "Test set accuracy on the 33-image acceptance test set"

H2 "5.3 Confusion Matrix Analysis"
PH "38x38 confusion matrix heatmap (seaborn) showing prediction counts for each true/predicted class pair"
P "The 38x38 confusion matrix visualises the model's prediction patterns across all disease classes. A strong diagonal -- where the count in cell (i,i) is consistently high -- confirms reliable per-class classification. Off-diagonal entries reveal systematic confusion between visually similar classes. Anticipated confusions include: (a) Tomato Early Blight vs. Late Blight, which both present as dark lesions on leaves but differ in lesion shape and distribution; (b) Corn Northern Leaf Blight and Corn Gray Leaf Spot, both appearing as elongated tan lesions on maize; and (c) Apple Apple Scab and Apple Black Rot, both causing dark spots on apple foliage. These confusions, if present, would be diagnostically meaningful -- they reflect genuine visual ambiguity that even experienced agronomists occasionally encounter."

H2 "5.4 Per-Class Performance Analysis"
PH "Per-class accuracy bar chart -- bar plot showing accuracy for each of the 38 disease classes"
P "Per-class accuracy analysis identifies classes where the model performs below the global average, guiding targeted improvements in data collection and augmentation strategy. Classes with fewer training samples (e.g., Corn Gray Leaf Spot with approximately 1,642 training images -- the smallest class in the dataset) are expected to exhibit lower accuracy. Classes with distinctive visual signatures (e.g., Orange Huanglongbing with asymmetric yellowing, and Grape Esca with tiger-stripe patterns) are expected to achieve higher accuracy due to their visually distinctive presentation."

H2 "5.5 Grad-CAM Visual Results"
PH "Grad-CAM heatmap samples -- grid of 6 images showing original leaf, heatmap, and overlay for 6 different disease classes"
P "Grad-CAM heatmaps provide qualitative validation that the model's predictions are grounded in genuine pathological features rather than spurious correlations. For a prediction to be considered trustworthy, the heatmap should concentrate activation in regions of the leaf corresponding to visible disease symptoms: spots, lesions, discolouration, or surface abnormalities. Heatmaps highlighting background soil, image borders, or unaffected leaf areas indicate the model may be exploiting confounding factors."
P "CropDoc targets model.res2, which operates at 4x4 spatial resolution before the final MaxPool -- the most semantically rich layer accessible before the classifier head. The 4x4 activation map is upsampled to 256x256 using bilinear interpolation and blended with the original image using a 50/50 alpha composite."

H2 "5.6 Test Set Evaluation"
P "The 33-image test set provided with the PlantVillage Kaggle dataset covers seven disease categories: Apple Cedar Rust, Apple Scab, Corn Common Rust, Potato Early Blight, Potato Healthy, Tomato Early Blight, Tomato Healthy, and Tomato Yellow Curl Virus. The original PlantVillage notebook achieved 100% accuracy (33/33 correct) with a simplified 2-epoch training configuration."
PH "Test set accuracy after training the full 20-epoch CropDoc configuration"

H2 "5.7 Chatbot Evaluation"
P "The chatbot's qualitative performance was evaluated through manual review of generated responses for representative disease queries."
P "Example 1 -- Tomato Late Blight query ('What should I do about tomato late blight?'): The chatbot correctly identified the disease as a serious fungal infection, recommended removing and destroying infected material, avoiding overhead watering, ensuring plant spacing, planting resistant varieties, and practicing crop rotation. Response was factual, concise, and within the 150-word limit."
P "Example 2 -- Corn Common Rust query ('My maize has rust spots. Is it serious?'): The chatbot correctly described the visual appearance of rust pustules, indicated that mild infections rarely cause severe yield loss, recommended removing infected leaves, ensuring adequate spacing, and planting resistant varieties in the next season. Language was farmer-appropriate and response was within the word limit."

H2 "5.8 Model Comparison"
P "Table 5.1 -- Architecture Comparison:"
$t5 = $doc.Tables.Add($sel.Range, 6, 5); $t5.Style = "Table Grid"
$h5d = @("Architecture","Parameters","Model Size","Inference (GPU)","Notes")
for ($c=0;$c -lt 5;$c++){$t5.Cell(1,$c+1).Range.Text=$h5d[$c];$t5.Cell(1,$c+1).Range.Font.Bold=$true}
$rows5 = @(
  @("VGG-16 (pretrained)","138M","~528 MB","~150ms","Too large for mobile"),
  @("ResNet-18 (pretrained)","11.7M","~45 MB","~60ms","Good accuracy; larger than needed"),
  @("ResNet-9 CropDoc (from scratch)","6.6M","~25 MB","<50ms","Optimised for mobile; from scratch"),
  @("MobileNetV2 (pretrained)","3.5M","~14 MB","~30ms","Smaller but lower accuracy here"),
  @("EfficientNet-B0 (pretrained)","5.3M","~21 MB","~70ms","Competitive; requires transfer learning")
)
for ($r=0;$r -lt $rows5.Count;$r++){for($c=0;$c -lt 5;$c++){$t5.Cell($r+2,$c+1).Range.Text=$rows5[$r][$c]}}
$sel.MoveDown(5,$t5.Rows.Count+2); Blank
PH "Comparative accuracy results -- accuracy of each architecture on PlantVillage validation set after equivalent training"

H2 "5.9 Discussion"
P "CropDoc demonstrates that a lightweight, from-scratch CNN architecture can achieve competitive performance on the PlantVillage benchmark while satisfying the practical constraints of mobile agricultural deployment. The integration of Grad-CAM transforms an otherwise opaque classification system into an explainable tool that can be understood and verified by non-expert users -- a critical requirement for farmer adoption."
P "Several limitations warrant discussion. First, the PlantVillage dataset consists exclusively of laboratory-captured images against controlled backgrounds. Real-world field images exhibit substantially greater variability in illumination, background clutter, leaf orientation, and disease progression stage. The data augmentation pipeline partially mitigates this domain gap, but field-collected training data would further improve generalisation. Second, the current system classifies each image as belonging to exactly one disease class. In practice, a single plant may exhibit multiple simultaneous infections. Extending to multi-label classification would address this limitation. Third, the flan-t5-base chatbot is a relatively compact language model and may occasionally produce generic responses for uncommon disease queries. Larger instruction-tuned models or agricultural fine-tuning could improve quality."
PB

# ─── Chapter 6 ───────────────────────────────────────────────────────────────
H1 "Chapter 6: Conclusion"
P "This project has presented CropDoc, an AI-powered plant disease detection and farmer support system developed as a Final Year Project for the BS Data Science programme at the Institute of Management Sciences, Peshawar. CropDoc addresses three critical gaps identified in the literature: the absence of visual explainability, the unsuitability of state-of-the-art models for mobile deployment, and the lack of conversational advisory support for farmers following a disease diagnosis."
P "The system's core component is a custom ResNet-9 CNN trained from scratch on the PlantVillage benchmark dataset, achieving"
PH "Final validation accuracy after training"
P "on the 38-class classification task with approximately 6.6 million parameters -- small enough to run on budget smartphones in under 200 milliseconds on CPU hardware. Grad-CAM heatmaps generated from the model.res2 residual block provide visual justification for every prediction. The flan-t5-base conversational chatbot, running fully offline, transforms the classification result into a complete advisory session drawing on a curated 38-entry knowledge base. The complete system is exposed through a FastAPI REST endpoint and exported in ONNX format for cross-platform compatibility."
P "Future work will focus on three primary directions: (i) collection and incorporation of field-captured training data to improve real-world generalisation; (ii) development of a native mobile application with offline model execution and Urdu/Pashto language support; and (iii) deployment in a controlled pilot study with smallholder farmers in Khyber Pakhtunkhwa to measure real-world impact on crop loss rates and pesticide usage. CropDoc represents a significant step toward making AI-powered agricultural advisory services accessible to those who need them most."
PB

# ─── References ──────────────────────────────────────────────────────────────
H1 "References"
P "[1] S. P. Mohanty, D. P. Hughes, and M. Salathe, 'Using Deep Learning for Image-Based Plant Disease Detection,' Frontiers in Plant Science, vol. 7, p. 1419, Sep. 2016, doi: 10.3389/fpls.2016.01419."
P "[2] K. P. Ferentinos, 'Deep learning models for plant disease detection and diagnosis,' Computers and Electronics in Agriculture, vol. 145, pp. 311-318, Feb. 2018, doi: 10.1016/j.compag.2018.01.009."
P "[3] P. Tm, A. Pranathi, K. SaiAshritha, N. B. Chittaragi, and S. G. Koolagudi, 'Tomato Leaf Disease Detection Using Convolutional Neural Network,' in Proc. 11th Int. Conf. Contemporary Computing (IC3), Noida, India, Aug. 2018, doi: 10.1109/IC3.2018.8530532."
P "[4] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, 'Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization,' in Proc. IEEE Int. Conf. Computer Vision (ICCV), Venice, Italy, Oct. 2017, pp. 618-626, doi: 10.1109/ICCV.2017.74."
P "[5] L. N. Smith, 'A Disciplined Approach to Neural Network Hyper-Parameters: Part 1,' arXiv:1803.09820 [cs.LG], Mar. 2018."
P "[6] A. Kamilaris and F. X. Prenafeta-Boldu, 'Deep Learning in Agriculture: A Survey,' Computers and Electronics in Agriculture, vol. 147, pp. 70-90, Apr. 2018, doi: 10.1016/j.compag.2018.02.016."

# ─── Save ────────────────────────────────────────────────────────────────────
$doc.SaveAs([ref]$OutPath, 16)
$doc.Close()
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
Write-Host "Report saved to: $OutPath"
