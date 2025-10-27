from langchain_community.document_loaders import PyPDFLoader

# Specify the path to your PDF
pdf_path = "2312_10997v5.pdf"

# Initialize the PDF loader
loader = PyPDFLoader("2312_10997v5.pdf")

# Load the PDF
documents = loader.load()

# Display basic information about the loaded documents
print(f"Total number of pages loaded: {len(documents)}")

# Print the first document's content as a demonstration
print("\n--- First Page Content ---")
print(documents[0].page_content)