# Import required libraries for file operations and randomization
import os  # Operating system interface for file path operations
import shutil  # High-level file operations (copying files)
import random  # Random number generation for dataset shuffling
from pathlib import Path  # Object-oriented filesystem paths

def create_directory(directory):
    """
    Create a directory and its parent directories if they don't exist.
    
    Args:
        directory (str): Path to the directory to be created
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

def split_dataset(source_dir, train_dir, val_dir, test_dir, train_ratio=0.7, val_ratio=0.15):
    """
    Split a hierarchical image dataset into training, validation, and test sets.
    Maintains the class directory structure in the split datasets.
    
    Args:
        source_dir (str): Path to source directory containing class folders
        train_dir (str): Path to training directory
        val_dir (str): Path to validation directory
        test_dir (str): Path to test directory
        train_ratio (float): Proportion of data for training (default: 0.7 or 70%)
        val_ratio (float): Proportion of data for validation (default: 0.15 or 15%)
                          (remaining 0.15 or 15% will be used for test data)
    
    Structure:
        source_dir/
            class1/
                image1.jpg
                image2.jpg
            class2/
                image3.jpg
                image4.jpg
    """
    # Create main output directories for train/val/test splits
    for dir_path in [train_dir, val_dir, test_dir]:
        create_directory(dir_path)

    # Get list of class directories (excluding any regular files)
    class_dirs = [d for d in os.listdir(source_dir)
                  if os.path.isdir(os.path.join(source_dir, d))]
    
    # Process each class directory separately
    for class_name in class_dirs:
        print(f"Processing {class_name}...")
        
        # Create class-specific directories in train, val, and test
        for dir_path in [train_dir, val_dir, test_dir]:
            create_directory(os.path.join(dir_path, class_name))
        
        # Get all image files from the current class directory
        class_dir = os.path.join(source_dir, class_name)
        image_files = [f for f in os.listdir(class_dir)
                       if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Skip if no images found in the class directory
        if not image_files:
            print(f"No images found in {class_name}")
            continue
        
        # Randomly shuffle files before splitting
        random.shuffle(image_files)
        
        # Calculate number of files for each split
        n_files = len(image_files)
        n_train = int(n_files * train_ratio)
        n_val = int(n_files * val_ratio)
        
        # Split file list into train, validation and test sets
        train_files = image_files[:n_train]  # First train_ratio of files
        val_files = image_files[n_train:n_train + n_val]  # Next val_ratio of files
        test_files = image_files[n_train + n_val:]  # Remaining files
        
        # Copy files to respective directories while maintaining structure
        for files, dest_dir in [
            (train_files, train_dir),
            (val_files, val_dir),
            (test_files, test_dir)
        ]:
            for f in files:
                src = os.path.join(class_dir, f)  # Source file path
                dst = os.path.join(dest_dir, class_name, f)  # Destination file path
                shutil.copy2(src, dst)  # Copy file with metadata
        
        # Print summary for current class
        print(f"{class_name}: {len(train_files)} train, {len(val_files)} val, {len(test_files)} test")

def main():
    """
    Main function to execute the dataset splitting process.
    Sets up directories and initiates the splitting process.
    """
    # Set random seed for reproducible splits
    random.seed(42)
    
    # Define directory structure
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
    source_dir = os.path.join(base_dir, "natural_images", "raw")  # Raw data
    train_dir = os.path.join(base_dir, "natural_images", "train")  # Training split
    val_dir = os.path.join(base_dir, "natural_images", "val")      # Validation split
    test_dir = os.path.join(base_dir, "natural_images", "test")    # Test split
    
    # Verify source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist!")
        print("Please create the directory and add your dataset.")
        return
    
    # Execute splitting process
    print("Starting dataset preparation...")
    print(f"Source directory: {source_dir}")
    split_dataset(source_dir, train_dir, val_dir, test_dir)
    
    # Print completion message and output directories
    print("\nDataset preparation completed!")
    print(f"Training data: {train_dir}")
    print(f"Validation data: {val_dir}")
    print(f"Test data: {test_dir}")

if __name__ == "__main__":
    main()
