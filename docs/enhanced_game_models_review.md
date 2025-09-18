# Enhanced Game Models Code Review

## Overview
Review of `/src/ml/enhanced_game_models.py` focusing on model architecture, ensemble voting, feature engineering, memory usage, and stacking implementation.

## 1. Model Architecture Choices

### ✅ Strengths
- **Diverse Algorithm Selection**: Good combination of LightGBM (gradient boosting), CatBoost (categorical handling), and Deep Neural Network (non-linear patterns)
- **Reasonable Hyperparameters**: Parameters are well-tuned for each model type
- **Complementary Approaches**: Tree-based models complement the neural network approach

### ⚠️ Concerns
- **LightGBM Configuration**: `max_depth=12` is quite deep and could lead to overfitting
- **Neural Network Complexity**: 5-layer network (150→100→75→50→25) may be overly complex for typical NFL datasets
- **No Cross-Validation for Individual Models**: Only the stacking classifier uses CV (5-fold)

### 🔧 Recommendations
```python
# More conservative LightGBM settings
self.models['lightgbm'] = LGBMClassifier(
    n_estimators=200,
    max_depth=8,  # Reduced from 12
    learning_rate=0.08,
    num_leaves=31,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=5,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

# Simpler neural network
self.models['deep_nn'] = MLPClassifier(
    hidden_layer_sizes=(100, 50, 25),  # Reduced complexity
    activation='relu',
    solver='adam',
    alpha=0.01,  # Increased regularization
    batch_size=32,
    learning_rate='adaptive',
    learning_rate_init=0.001,
    max_iter=500,
    early_stopping=True,
    validation_fraction=0.1,
    random_state=42
)
```

## 2. Ensemble Voting Weights

### ⚠️ Major Issues
- **Hardcoded Weights**: Weights are fixed without empirical validation
- **Equal Tree Model Weighting**: LightGBM and CatBoost both get 0.3, but performance may differ
- **No Dynamic Weight Adjustment**: No mechanism to adjust weights based on validation performance

### 🚨 Critical Problem
```python
# Current approach (problematic)
weights = {
    'lightgbm': 0.3,   # No justification
    'catboost': 0.3,   # No justification  
    'deep_nn': 0.2,    # No justification
    'stacking': 0.2    # No justification
}
```

### 🔧 Recommended Fix
```python
def calculate_optimal_weights(self, X_val, y_val):
    """Calculate weights based on validation performance"""
    individual_scores = {}
    
    for name, model in self.models.items():
        y_pred = model.predict(X_val)
        score = accuracy_score(y_val, y_pred)
        individual_scores[name] = score
    
    # Weight by relative performance
    total_score = sum(individual_scores.values())
    weights = {name: score/total_score 
              for name, score in individual_scores.items()}
    
    return weights
```

## 3. Feature Engineering Logic

### ✅ Strengths
- **Safe Column Checking**: Properly checks if columns exist before using them
- **Meaningful Features**: Momentum, power differentials, and temporal features are relevant
- **No Data Modification**: Creates copies instead of modifying original data

### ⚠️ Potential Issues
- **Division by Zero Protection**: Uses `+ 1` but could still cause numerical instability
- **Feature Scaling Order**: Features are added before scaling, which is correct

### 🔍 Specific Analysis
```python
# Good: Safe column existence check
if 'recent_wins' in X.columns and 'recent_losses' in X.columns:
    X_enhanced['momentum_score'] = (
        X['recent_wins'] - X['recent_losses']
    ) / (X['recent_wins'] + X['recent_losses'] + 1)  # +1 prevents division by zero

# Good: Reasonable interaction features
if 'home_power_rating' in X.columns and 'away_power_rating' in X.columns:
    X_enhanced['power_diff_squared'] = (
        X['home_power_rating'] - X['away_power_rating']
    ) ** 2
```

## 4. Memory Usage with Multiple Models

### 🚨 Critical Memory Issues

1. **Multiple Large Models in Memory**: Stores 4 complete models simultaneously
2. **No Memory Management**: No cleanup or model unloading capabilities
3. **Redundant Feature Storage**: Enhanced features created multiple times
4. **Large Neural Network**: 5-layer network with large hidden sizes

### 📊 Estimated Memory Usage
- **LightGBM**: ~50-100MB (depending on trees)
- **CatBoost**: ~50-100MB  
- **Deep Neural Network**: ~10-20MB (weights)
- **Stacking Model**: Additional ~50MB (contains copies of base models)
- **Feature Data**: ~2-5x original dataset size (enhanced features)

**Total Estimated**: ~200-400MB per model instance

### 🔧 Memory Optimization Recommendations
```python
def optimize_memory(self):
    """Optimize memory usage"""
    
    # Option 1: Lazy loading
    def get_model(self, model_name):
        if model_name not in self._loaded_models:
            self._loaded_models[model_name] = joblib.load(f'models/{model_name}.pkl')
        return self._loaded_models[model_name]
    
    # Option 2: Feature caching
    @lru_cache(maxsize=128)
    def _cached_feature_engineering(self, X_hash):
        return self.add_advanced_features(X)
    
    # Option 3: Model pruning for tree models
    def prune_models(self):
        for name, model in self.models.items():
            if hasattr(model, 'n_estimators'):
                # Reduce trees if memory constrained
                model.n_estimators = min(model.n_estimators, 100)
```

## 5. Stacking Implementation Correctness

### ✅ Correct Implementation
- **Proper CV**: Uses 5-fold cross-validation to prevent overfitting
- **Separate Meta-Model**: Uses different algorithm (LightGBM) as meta-learner
- **Base Model Selection**: Excludes neural network from stacking (good choice due to training time)

### ⚠️ Potential Issues
- **No Stratification**: CV doesn't specify stratification for imbalanced classes
- **Meta-Model Complexity**: Meta-model might be too complex for NFL prediction

### 🔍 Stacking Analysis
```python
# Current implementation (mostly correct)
base_models = [
    ('lightgbm', self.models['lightgbm']),
    ('catboost', self.models['catboost'])  # Good: Only tree models
]

meta_model = LGBMClassifier(
    n_estimators=100,  # Reasonable
    max_depth=5,       # Good: Simpler than base models
    learning_rate=0.1, # Reasonable
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)

self.models['stacking'] = StackingClassifier(
    estimators=base_models,
    final_estimator=meta_model,
    cv=5,  # Should add stratify=True
    n_jobs=-1
)
```

## 6. Data Leakage Analysis

### ✅ No Obvious Data Leakage
- **Proper Fit/Transform Pattern**: Scaler is fit on training data, then transforms test data
- **Feature Engineering**: Applied consistently to both train and test
- **No Future Information**: Features don't use future game information

### 🔍 Data Flow Verification
```python
# Training (correct)
X_enhanced = self.add_advanced_features(X)      # No leakage
X_scaled = self.scaler.fit_transform(X_enhanced) # Fit on train
self.ensemble.fit(X_scaled, y)

# Prediction (correct)  
X_enhanced = self.add_advanced_features(X)      # Same transformation
X_scaled = self.scaler.transform(X_enhanced)    # Transform only
predictions = self.ensemble.predict(X_scaled)
```

## 7. Scaling Implementation

### ✅ Proper Scaling
- **StandardScaler**: Appropriate for neural networks and mixed algorithms
- **Fit/Transform Pattern**: Correctly implemented
- **Applied After Feature Engineering**: Correct order of operations

## Summary and Priority Recommendations

### 🚨 High Priority Issues
1. **Hardcoded Ensemble Weights**: Implement validation-based weight calculation
2. **Memory Usage**: Add memory optimization for production deployment
3. **Overfitting Risk**: Reduce model complexity (tree depth, neural network size)

### 📊 Medium Priority Issues  
1. **Cross-Validation**: Add stratification for imbalanced classes
2. **Hyperparameter Tuning**: Implement automated hyperparameter optimization
3. **Feature Selection**: Add feature importance-based selection

### ✅ Working Well
1. **Data leakage prevention**
2. **Feature engineering safety**
3. **Stacking implementation**
4. **Model diversity**

### 🎯 Recommended Changes
1. Replace hardcoded weights with validation-based weights
2. Add memory management capabilities
3. Implement model pruning options
4. Add stratified CV for stacking
5. Consider reducing neural network complexity

The code shows good understanding of ensemble methods but needs optimization for production use, particularly around memory management and dynamic weight calculation.