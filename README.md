# FoodvisorLM 🍎
A webapp to find potentially harmful ingredients in packaged food and find similar products built using AWS OpenSearch, SageMaker, DynamoDB, Cognito, Docker, Flask, and OpenAI API.
[Demo](https://www.linkedin.com/posts/anudeep-tubati_ai-machinelearning-cloudcomputing-activity-7158624067665711105-5doF?utm_source=share&utm_medium=member_desktop)

### Sample Data
Use this data to test the barcode scanner or the search feature.
| Product Code | Image | Name | Description | Ingredients |
| --- | --- | --- | --- | --- |
| 8904063230126 | ![barcode 8904063230126](/assets/sample_barcodes/8904063230126.jpg) | Haldiram's Navrattan | Spicy snacks mixture of split chickpeas, peanuts, and sundried potato chips | chickpeas flour, vegetable oil (cotton seed, corn, palmolein), puy lentil, peanuts, acidity regulator [citric acid powder (E330)], anticaking agent [silicon dioxide (E551)]
| 074570014002 | ![barcode 074570014002](/assets/sample_barcodes/074570014002.jpg) | Haagen-Dazs | chocolate ice cream, chocolate | cream, skim milk, cane sugar, cocoa processed with alkali, egg yolks
| 054467050351 | ![barcode 054467050351](/assets/sample_barcodes/054467050351.jpg) | Starbucks | double chocolate hot cocoa mix, double chocolate | cane sugar, cocoa, cocoa (processed with alkali), dark chocolate (sugar, chocolate mass, cocoa butter, soy lecithin), natural vanilla flavor

### Background
While I find [Yuka](https://yuka.io/en/) very useful for this, I started this project with two questions:
1) How can the recent advances in NLP help summarize research in health and food science per ingredient?
2) Since the ratings by a human expert may induce bias, is a qualitative stance better than Yuka's rating system?

Data is fetched from the [US Department of Agriculture](https://fdc.nal.usda.gov/download-datasets.html) archive. A subset is derived based on popular brands like Haagen-Dazs and Starbucks; look at [products](/assets/products_info.csv) for the list of all supported products.

### Setting up
Prerequisite - Set all the environment variables in [env.list](/env.list)
```bash
git clone https://github.com/NeuralFlux/foodvisorLM
cd foodvisorLM
pip install -r requirements.txt
cd flask-app/
flask --app app.py --debug run

# build Docker image
cd ..
docker build -t fvsr-lm .
docker run --env-file env.list -p 5000:5000 fvsr-lm
```

### Architecture Diagram
![Architecture diagram of this project comprising various AWS services](/assets/foodvisorLM_arch.png)

### Design Choices
#### Web hosting
| AWS Service | Pros and Cons |
| --- | --- |
| Lambda | Scalable but cold-starts are slow |
| S3 | Scalable but static pages only |
| Amplify | Scalable and JavaScript-based whereas this app uses Flask for lightweight API |
| Lightsail | Load balancing, isolated, free tier but no blue/green deployments and auto scaling |
| Elastic Beanstalk | Robust solution but insufficient free tier EC2 credits |

#### Database
Product barcode data is largely structured and contains millions of rows, hence RDS or DynamoDB are well-suited. However, for User History, DynamoDB is better suited due to scalability.

### Future Ideas
- [ ] Deploy custom retrieval-augmented generation pipeline for label classification
- [ ] Cite relevant articles in RAG
- [ ] Recommend healthier alternatives as opposed to similar products only

This is a part of my project for Cloud Computing and Big Data at New York University, Fall 2023 taught by Prof. Sambit Sahu.

### References
1. A. Hill, “What AWS service should you use to publish a web site?, ” https://adrianhall.github.io/cloud/2019/01/31/which-aws-service-for-hosting/
2. OpenAI, “Chat Completion API Documentation, ” https://platform.openai.com/docs/guides/text-generation/chat-completions-api
3. AWS, “AWS Documentation, ” https://docs.aws.amazon.com/index.html
4. Julie, François, Benoı̂t, “Yuka Blog, ” https://yuka.io/en/
5. OpenSearch, "Neural Search Tutorial, " https://opensearch.org/docs/latest/search-plugins/neural-search-tutorial/
6. Ricardo Ferreira, "Developing Neural Searches with Custom Models, " https://community.aws/content/2ZVEF1vMg0Jh2IwtbVMEVEMND59/developing-neural-searches-with-custom-models?lang=en
