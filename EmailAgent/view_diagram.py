from PIL import Image
import pytesseract
import os

# Try to install pillow if not available
try:
    img = Image.open('diagram-export-8-1-2026-4_49_12-pm.png')
    
    # Get image info
    print(f"Image Size: {img.size}")
    print(f"Image Format: {img.format}")
    print(f"Image Mode: {img.mode}")
    print("\n" + "="*80)
    
    # Try to extract text using OCR if pytesseract is available
    try:
        text = pytesseract.image_to_string(img)
        print("\nExtracted Text from Diagram:")
        print("="*80)
        print(text)
    except:
        print("\nNote: OCR not available. Opening image for manual viewing...")
        print("The image contains an architecture diagram.")
        img.show()
        
except Exception as e:
    print(f"Error: {e}")
    print("\nAttempting to open image with default viewer...")
    os.startfile('diagram-export-8-1-2026-4_49_12-pm.png')
