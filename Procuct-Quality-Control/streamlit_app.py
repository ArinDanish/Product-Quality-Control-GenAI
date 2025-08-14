import streamlit as st
import os
from visionllm import VisionQualityController
import tempfile

st.set_page_config(
    page_title="Product Quality Control Analyzer",
    page_icon="🔍",
    layout="wide"
)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temp directory and return the path"""
    if uploaded_file is not None:
        # Create a temporary file with the same extension as the uploaded file
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return temp_path
    return None

def main():
    st.title("Product Quality Control Analyzer 🔍")
    st.write("Upload a perfect reference image and a test image to analyze quality differences.")

    # Create two columns for image upload
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Perfect Reference Image")
        perfect_image = st.file_uploader("Upload perfect sample", type=['jpg', 'jpeg', 'png'], key="perfect")
        if perfect_image:
            st.image(perfect_image, caption="Reference Image", use_container_width=True)

    with col2:
        st.subheader("Test Image")
        test_image = st.file_uploader("Upload test sample", type=['jpg', 'jpeg', 'png'], key="test")
        if test_image:
            st.image(test_image, caption="Test Image", use_container_width=True)

    analyze_button = st.button("Analyze Quality", type="primary")

    if analyze_button and perfect_image and test_image:
        try:
            with st.spinner("Analyzing images..."):
                # Save uploaded files temporarily
                perfect_path = save_uploaded_file(perfect_image)
                test_path = save_uploaded_file(test_image)
                
                # Initialize the quality controller
                qc = VisionQualityController()
                
                # Analyze images
                analysis = qc.comparative_analysis(perfect_path, test_path)
                
                # Create columns for results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Original Test Image")
                    st.image(test_image, use_container_width=True)
                
                with col2:
                    st.subheader("Marked Defects")
                    if analysis.get("defects"):
                        # Mark defects on the image
                        marked_image = qc.mark_defects_on_image(test_path, analysis["defects"])
                        st.image(marked_image, use_container_width=True)
                    else:
                        st.info("No defects detected in the image.")

                if perfect_path and test_path:
                    # Initialize quality controller
                    qc = VisionQualityController()
                    
                    # Perform analysis
                    result = qc.comparative_analysis(perfect_path, test_path, "product")

                    # Display results
                    st.header("Analysis Results")
                    
                    # Show quality score if available
                    if result.get("quality_score"):
                        st.metric("Quality Score", f"{result['quality_score']}/10")
                    
                    # Show recommendation if available
                    if result.get("recommendation"):
                        recommendation = result["recommendation"]
                        if recommendation == "PASS":
                            st.success(f"Recommendation: {recommendation}")
                        elif recommendation == "FAIL":
                            st.error(f"Recommendation: {recommendation}")
                        else:
                            st.warning(f"Recommendation: {recommendation}")

                    # Show detailed analysis
                    st.subheader("Detailed Analysis")
                    st.markdown(result.get("raw_response", "No detailed analysis available"))

                    # Cleanup temporary files
                    os.remove(perfect_path)
                    os.remove(test_path)
                    os.rmdir(os.path.dirname(perfect_path))
        
        except Exception as e:
            st.error(f"An error occurred during analysis: {str(e)}")

    elif analyze_button:
        st.warning("Please upload both a perfect reference image and a test image to analyze.")

if __name__ == "__main__":
    main()
