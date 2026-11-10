# Weekly Hugging Face updates

Source: https://github.com/Double-FW/Accessibility-and-Inclusive-Design-Knowledge-Base

Destination: https://huggingface.co/datasets/GarethFW/Inclusive_Design_Library

The destination is fixed in export-config.json. Store the dataset-scoped Hugging Face token as repository secret `HF_TOKEN`. No `HF_DATASET_ID` variable is required. Create `.github/workflows/huggingface-sync.yml` from WORKFLOW_TO_COPY.txt in the setup download. Run it manually once, then weekly on Mondays at 07:23 UTC. The workflow validates the source and managed export before publishing. New or renamed articles require review of the export configuration.
