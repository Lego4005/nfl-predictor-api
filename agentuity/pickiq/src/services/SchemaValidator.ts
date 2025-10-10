/**
 * Schema Validator - Validates 83-bundle against JSON Schema
 */

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validatePredictionBundle(bundle: any): ValidationResult {
  const errors: string[] = [];
  
  if (!bundle.overall) {
    errors.push("Missing 'overall' object");
  } else {
    if (!bundle.overall.winner_team_id) errors.push("Missing overall.winner_team_id");
    if (typeof bundle.overall.home_win_prob !== 'number') errors.push("Missing/invalid overall.home_win_prob");
    if (typeof bundle.overall.overall_confidence !== 'number') errors.push("Missing/invalid overall.overall_confidence");
  }
  
  if (!Array.isArray(bundle.predictions)) {
    errors.push("'predictions' must be an array");
  } else {
    if (bundle.predictions.length !== 83) {
      errors.push(`Expected exactly 83 predictions, got ${bundle.predictions.length}`);
    }
    
    bundle.predictions.forEach((pred: any, idx: number) => {
      if (!pred.category) errors.push(`Prediction ${idx}: missing category`);
      if (!pred.subject) errors.push(`Prediction ${idx}: missing subject`);
      if (!pred.pred_type) errors.push(`Prediction ${idx}: missing pred_type`);
      if (pred.value === undefined) errors.push(`Prediction ${idx}: missing value`);
      if (typeof pred.confidence !== 'number') errors.push(`Prediction ${idx}: invalid confidence`);
      if (typeof pred.stake_units !== 'number') errors.push(`Prediction ${idx}: invalid stake_units`);
      if (!pred.odds) errors.push(`Prediction ${idx}: missing odds`);
      if (!Array.isArray(pred.why)) errors.push(`Prediction ${idx}: 'why' must be array`);
    });
  }
  
  return {
    valid: errors.length === 0,
    errors: errors
  };
}

export function repairBundle(bundle: any, errors: string[], categoryRegistry: any[]): any {
  if (bundle.predictions && bundle.predictions.length !== 83) {
    const currentCount = bundle.predictions.length;
    
    if (currentCount < 83) {
      const missingCount = 83 - currentCount;
      const existingCategories = new Set(bundle.predictions.map((p: any) => p.category));
      const missingCategories = categoryRegistry
        .filter(cat => !existingCategories.has(cat.id))
        .slice(0, missingCount);
      
      for (const cat of missingCategories) {
        bundle.predictions.push(createStubPrediction(cat));
      }
    } else if (currentCount > 83) {
      bundle.predictions = bundle.predictions.slice(0, 83);
    }
  }
  
  if (bundle.predictions) {
    bundle.predictions = bundle.predictions.map((pred: any) => ({
      category: pred.category || 'unknown',
      subject: pred.subject || 'game',
      pred_type: pred.pred_type || 'binary',
      value: pred.value !== undefined ? pred.value : false,
      confidence: typeof pred.confidence === 'number' ? pred.confidence : 0.5,
      stake_units: typeof pred.stake_units === 'number' ? pred.stake_units : 0,
      odds: pred.odds || { type: 'american', value: -110 },
      why: Array.isArray(pred.why) ? pred.why : []
    }));
  }
  
  if (!bundle.overall) {
    bundle.overall = {
      winner_team_id: 'home',
      home_win_prob: 0.5,
      away_win_prob: 0.5,
      overall_confidence: 0.5
    };
  }
  
  return bundle;
}

function createStubPrediction(category: any): any {
  let value: any = false;
  
  if (category.pred_type === 'numeric') {
    value = 24.5;
  } else if (category.pred_type === 'enum' && category.allowed) {
    value = category.allowed[0];
  }
  
  return {
    category: category.id,
    subject: category.subject || 'game',
    pred_type: category.pred_type,
    value: value,
    confidence: 0.5,
    stake_units: 0,
    odds: { type: 'american', value: -110 },
    why: []
  };
}
