# Import required libraries
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from torchvision import models
import matplotlib
matplotlib.use('TkAgg')  # Enable window display on Mac
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import time
from datetime import datetime
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

class NaturalImagesDataset(Dataset):
    """Custom Dataset class for loading natural images.
    Inherits from torch.utils.data.Dataset to enable DataLoader functionality."""
    
    def __init__(self, root_dir, transform=None):
        """Initialize the dataset with root directory and optional transforms.
        
        Args:
            root_dir (str): Path to the dataset directory
            transform (callable, optional): Optional transform to be applied on images
        """
        self.root_dir = root_dir
        self.transform = transform
        # Get sorted list of class names from directory names
        self.classes = sorted(os.listdir(root_dir))
        # Create a mapping from class names to numerical indices
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        self.images = []
        self.labels = []
        
        # Load all image paths and their corresponding labels
        for class_name in self.classes:
            class_dir = os.path.join(root_dir, class_name)
            if not os.path.isdir(class_dir):
                continue
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.images.append(os.path.join(class_dir, img_name))
                    self.labels.append(self.class_to_idx[class_name])

    def __len__(self):
        """Return the total number of images in the dataset."""
        return len(self.images)

    def __getitem__(self, idx):
        """Get a single item from the dataset by index.
        
        Returns:
            tuple: (image, label) where image is a transformed PIL Image and label is an integer
        """
        img_path = self.images[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            label = self.labels[idx]
            
            if self.transform:
                image = self.transform(image)
                
            return image, label
        except Exception as e:
            print(f"Error loading image {img_path}: {str(e)}")
            # Return a zero tensor if image loading fails
            return torch.zeros((3, 224, 224)), label

class CustomResNet(nn.Module):
    """Custom ResNet model based on ResNet18 architecture with modified final layers."""
    
    def __init__(self, num_classes=8):
        """Initialize the model with pretrained ResNet18 and custom final layers.
        
        Args:
            num_classes (int): Number of output classes
        """
        super(CustomResNet, self).__init__()
        # Load pretrained ResNet18 model
        self.resnet = models.resnet18(pretrained=True)
        # Modify the final fully connected layer for our classification task
        num_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),  # Add dropout for regularization
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        """Define the forward pass of the model."""
        return self.resnet(x)

def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train the model for one epoch.
    
    Args:
        model: The neural network model
        train_loader: DataLoader for training data
        criterion: Loss function
        optimizer: Optimization algorithm
        device: Device to run the training on (CPU/GPU)
    
    Returns:
        tuple: (epoch_loss, epoch_accuracy)
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (inputs, labels) in enumerate(train_loader):
        # Move data to appropriate device
        inputs, labels = inputs.to(device), labels.to(device)
        
        # Zero the parameter gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        
        # Backward pass and optimize
        loss.backward()
        optimizer.step()
        
        # Track statistics
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        # Print progress
        if (batch_idx + 1) % 20 == 0:
            print(f'Batch: {batch_idx + 1}/{len(train_loader)}, Loss: {loss.item():.4f}')
    
    # Calculate epoch statistics
    epoch_loss = running_loss / len(train_loader)
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc

def validate(model, val_loader, criterion, device):
    """Validate the model on validation data.
    
    Args:
        model: The neural network model
        val_loader: DataLoader for validation data
        criterion: Loss function
        device: Device to run the validation on (CPU/GPU)
    
    Returns:
        tuple: (validation_loss, validation_accuracy)
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():  # Disable gradient computation
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    val_loss = running_loss / len(val_loader)
    val_acc = 100. * correct / total
    return val_loss, val_acc

def plot_training_curves(train_losses, val_losses, train_accs, val_accs, save_dir):
    """Plot and save training and validation curves.
    
    Args:
        train_losses: List of training losses
        val_losses: List of validation losses
        train_accs: List of training accuracies
        val_accs: List of validation accuracies
        save_dir: Directory to save the plots
    """
    plt.figure(figsize=(12, 5))
    
    # Plot losses
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.title('Training and Validation Losses')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Plot accuracies
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Accuracy')
    plt.plot(val_accs, label='Val Accuracy')
    plt.title('Training and Validation Accuracies')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    
    plt.tight_layout()
    save_path = os.path.join(save_dir, 'training_curves.png')
    plt.savefig(save_path)
    plt.show()
    print(f"\nTraining curves saved to: {save_path}")

def plot_confusion_matrix(y_true, y_pred, classes, save_dir):
    """Plot and save confusion matrix.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        classes: List of class names
        save_dir: Directory to save the plot
    """
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    save_path = os.path.join(save_dir, 'confusion_matrix.png')
    plt.savefig(save_path)
    plt.show()
    print(f"\nConfusion matrix saved to: {save_path}")

def main():
    """Main function to run the training pipeline."""
    # Set random seed for reproducibility
    torch.manual_seed(42)
    
    # Set training parameters
    batch_size = 16  # Reduced for Mac
    num_epochs = 10
    learning_rate = 0.001
    
    # Set device (CPU for Mac)
    device = torch.device('cpu')
    print(f"Using device: {device}")
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'output_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory created: {output_dir}")
    
    # Define data transforms for training and validation
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),  # Data augmentation
        transforms.RandomRotation(10),      # Data augmentation
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet normalization
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Load datasets
    print("Loading datasets...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_dataset = NaturalImagesDataset(os.path.join(base_dir, 'natural_images/train'), transform=train_transform)
    val_dataset = NaturalImagesDataset(os.path.join(base_dir, 'natural_images/val'), transform=val_transform)
    test_dataset = NaturalImagesDataset(os.path.join(base_dir, 'natural_images/test'), transform=val_transform)
    
    print(f"\nFound {len(train_dataset)} training images")
    print(f"Found {len(val_dataset)} validation images")
    print(f"Found {len(test_dataset)} test images")
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Initialize model, loss function, and optimizer
    print("\nInitializing model...")
    model = CustomResNet(num_classes=len(train_dataset.classes))
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    print("\nStarting training...")
    train_losses, val_losses = [], []
    train_accs, val_accs = [], []
    best_val_acc = 0
    
    # Train for specified number of epochs
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch+1}/{num_epochs}")
        start_time = time.time()
        
        # Train one epoch and get metrics
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Validate and get metrics
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        # Save metrics for plotting
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)
        
        # Print epoch summary
        epoch_time = time.time() - start_time
        print(f"\nEpoch {epoch+1} Summary:")
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        print(f"Time: {epoch_time:.2f}s")
        
        # Save best model based on validation accuracy
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model_save_path = os.path.join(output_dir, 'best_model.pth')
            torch.save(model.state_dict(), model_save_path)
            print(f"\nNew best model saved to: {model_save_path}")
    
    # Plot training curves
    print("\nPlotting training curves...")
    plot_training_curves(train_losses, val_losses, train_accs, val_accs, output_dir)
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    model.eval()
    all_preds = []
    all_labels = []
    
    # Get predictions for test set
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
    
    # Generate and plot confusion matrix
    print("\nGenerating confusion matrix...")
    plot_confusion_matrix(all_labels, all_preds, train_dataset.classes, output_dir)
    
    # Print detailed classification report
    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=train_dataset.classes))
    
    print(f"\nTraining completed! All outputs saved to: {output_dir}")

if __name__ == "__main__":
    main()