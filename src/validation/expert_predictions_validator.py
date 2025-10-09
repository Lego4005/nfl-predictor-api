"""
Expert Predictions Validator - Enforces exactly 83 assertions with schema compliance
Hard gate: reject entire bundle on any validation failure
"""

import json
from typort Dict, Any, List, Optional, Tuple
from pathlib import Path
import jsonschema
from loguru import logger

from src.config import settings


class ExpertPredictionsValidator:
    """
    Validates expert prediction bundles against schema and business rules
    Enforces exactly 83 assertions with proper constraints
    """

    def __init__(self):
        self.schema = self._load_schema()
        self.category_registry = self._load_category_registry()

    def validate_prediction_bundle(
        self,
        expert_id: str,
        game_id: str,
        predictions: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate complete prediction bundle

        Args:
            expert_id: Expert identifier
            game_id: Game identifier
            predictions: Prediction bundle to validate

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        try:
            # 1. JSON Schema validation
            schema_errors = self._validate_json_schema(predictions)
            if schema_errors:
                errors.extend(schema_errors)
                return False, errors

            # 2. Exactly 83 assertions check
            assertion_errors = self._validate_assertion_count(predictions)
            if assertion_errors:
                errors.extend(assertion_errors)
                return False, errors

            # 3. Category coverage validation
            coverage_errors = self._validate_category_coverage(predictions)
            if coverage_errors:
                errors.extend(coverage_errors)
                return False, errors

            # 4. Individual assertion validation
            for i, assertion in enumerate(predictions.get('predictions', [])):
                assertion_errors = self._validate_single_assertion(assertion, i)
                if assertion_errors:
                    errors.extend(assertion_errors)

            # 5. Stake and odds validation
            stake_errors = self._validate_stakes_and_odds(predictions)
            if stake_errors:
                errors.extend(stake_errors)

            # 6. Business rule validation
            business_errors = self._validate_business_rules(expert_id, predictions)
            if business_errors:
                errors.extend(business_errors)

            if errors:
                logger.warning(f"Validation failed for {expert_id} on {game_id}", {
                    "error_count": len(errors),
                    "errors": errors[:5]  # Log first 5 errors
                })
                return False, errors

            logger.info(f"Validation passed for {expert_id} on {game_id}")
            return True, []

        except Exception as e:
            logger.error(f"Validation exception for {expert_id}: {e}")
            return False, [f"Validation system error: {str(e)}"]

    def _validate_json_schema(self, predictions: Dict[str, Any]) -> List[str]:
        """Validate against JSON schema"""
        try:
            jsonschema.validate(predictions, self.schema)
            return []
        except jsonschema.ValidationError as e:
            return [f"Schema validation failed: {e.message} at {e.json_path}"]
        except Exception as e:
            return [f"Schema validation error: {str(e)}"]

    def _validate_assertion_count(self, predictions: Dict[str, Any]) -> List[str]:
        """Enforce exactly 83 assertions"""
        prediction_list = predictions.get('predictions', [])

        if len(prediction_list) != 83:
            return [f"Expected exactly 83 predictions, got {len(prediction_list)}"]

        return []

    def _validate_category_coverage(self, predictions: Dict[str, Any]) -> List[str]:
        """Validate all required categories are covered"""
        prediction_list = predictions.get('predictions', [])

        # Get all categories from predictions
        predicted_categories = set()
        for pred in prediction_list:
            category = pred.get('category')
            subject = pred.get('subject', '')
            # Create unique key for category + subject combinations
            predicted_categories.add(f"{category}:{subject}")

        # Check against expected categories from registry
        expected_categories = set()
        for category_info in self.category_registry.values():
            category = category_info['category']
            subjects = category_info.get('subjects', [''])
            for subject in subjects:
                expected_categories.add(f"{category}:{subject}")

        missing = expected_categories - predicted_categories
        extra = predicted_categories - expected_categories

        errors = []
        if missing:
            errors.append(f"Missing required categories: {sorted(list(missing))[:5]}")
        if extra:
            errors.append(f"Unexpected categories: {sorted(list(extra))[:5]}")

        return errors

    def _validate_single_assertion(
        self,
        assertion: Dict[str, Any],
        index: int
    ) -> List[str]:
        """Validate individual assertion"""
        errors = []

        # Required fields
        required_fields = ['category', 'subject', 'pred_type', 'value', 'confidence', 'stake_units', 'odds']
        for field in required_fields:
            if field not in assertion:
                errors.append(f"Assertion {index}: Missing required field '{field}'")

        # Confidence bounds
        confidence = assertion.get('confidence')
        if confidence is not None:
            if not (0.0 <= confidence <= 1.0):
                errors.append(f"Assertion {index}: Confidence {confidence} not in [0,1]")

        # Stake units validation
        stake_units = assertion.get('stake_units')
        if stake_units is not None:
            if stake_units < 0:
                errors.append(f"Assertion {index}: Negative stake_units {stake_units}")
            if stake_units > float(settings.MAX_STAKE_UNITS_PER_BET):
                errors.append(f"Assertion {index}: Stake {stake_units} exceeds max {settings.MAX_STAKE_UNITS_PER_BET}")

        # Prediction type validation
        pred_type = assertion.get('pred_type')
        if pred_type not in ['binary', 'enum', 'numeric']:
            errors.append(f"Assertion {index}: Invalid pred_type '{pred_type}'")

        # Category-specific validation
        category = assertion.get('category')
        if category in self.category_registry:
            category_errors = self._validate_category_specific(assertion, index)
            errors.extend(category_errors)

        return errors

    def _validate_category_specific(
        self,
        assertion: Dict[str, Any],
        index: int
    ) -> List[str]:
        """Validate category-specific constraints"""
        errors = []
        category = assertion.get('category')
        category_info = self.category_registry.get(category, {})

        # Value constraints
        value = assertion.get('value')
        constraints = category_info.get('constraints', {})

        if 'min_value' in constraints and isinstance(value, (int, float)):
            if value < constraints['min_value']:
                errors.append(f"Assertion {index}: Value {value} below minimum {constraints['min_value']}")

        if 'max_value' in constraints and isinstance(value, (int, float)):
            if value > constraints['max_value']:
                errors.append(f"Assertion {index}: Value {value} above maximum {constraints['max_value']}")

        if 'valid_values' in constraints:
            if value not in constraints['valid_values']:
                errors.append(f"Assertion {index}: Value '{value}' not in valid set {constraints['valid_values']}")

        return errors

    def _validate_stakes_and_odds(self, predictions: Dict[str, Any]) -> List[str]:
        """Validate stakes and odds across all predictions"""
        errors = []
        prediction_list = predictions.get('predictions', [])

        total_stake = sum(pred.get('stake_units', 0) for pred in prediction_list)

        # Check total stake reasonable (not enforced as hard limit)
        if total_stake > 500:  # Warning threshold
            errors.append(f"Warning: Total stake {total_stake} is very high")

        # Validate odds format
        for i, pred in enumerate(prediction_list):
            odds = pred.get('odds')
            if odds is not None and not self._is_valid_odds_format(odds):
                errors.append(f"Assertion {i}: Invalid odds format '{odds}'")

        return errors

    def _validate_business_rules(
        self,
        expert_id: str,
        predictions: Dict[str, Any]
    ) -> List[str]:
        """Validate business-specific rules"""
        errors = []

        # Check memory references exist
        memory_refs = predictions.get('memory_references', [])
        if not memory_refs:
            errors.append("Warning: No memory references provided")

        # Validate overall confidence
        overall_confidence = predictions.get('overall_confidence')
        if overall_confidence is not None:
            if not (0.0 <= overall_confidence <= 1.0):
                errors.append(f"Overall confidence {overall_confidence} not in [0,1]")

        return errors

    def _is_valid_odds_format(self, odds: Any) -> bool:
        """Check if odds are in valid format (American, decimal, or fractional)"""
        if isinstance(odds, (int, float)):
            return True  # Numeric odds

        if isinstance(odds, str):
            # American odds (+/-100)
            if odds.startswith(('+', '-')) and odds[1:].isdigit():
                return True
            # Decimal odds (1.50)
            try:
                float(odds)
                return True
            except ValueError:
                pass
            # Fractional odds (3/2)
            if '/' in odds:
                parts = odds.split('/')
                if len(parts) == 2 and all(part.isdigit() for part in parts):
                    return True

        return False

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema for validation"""
        schema_path = Path("schemas/expert_predictions_v1.schema.json")

        if not schema_path.exists():
            logger.warning(f"Schema file not found: {schema_path}")
            return self._get_default_schema()

        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return self._get_default_schema()

    def _load_category_registry(self) -> Dict[str, Any]:
        """Load category registry with constraints"""
        registry_path = Path("config/category_registry.json")

        if not registry_path.exists():
            logger.warning(f"Category registry not found: {registry_path}")
            return self._get_default_registry()

        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load category registry: {e}")
            return self._get_default_registry()

    def _get_default_schema(self) -> Dict[str, Any]:
        """Default schema if file not found"""
        return {
            "type": "object",
            "required": ["expert_id", "game_id", "predictions"],
            "properties": {
                "expert_id": {"type": "string"},
                "game_id": {"type": "string"},
                "predictions": {
                    "type": "array",
                    "minItems": 83,
                    "maxItems": 83,
                    "items": {
                        "type": "object",
                        "required": ["category", "subject", "pred_type", "value", "confidence", "stake_units", "odds"],
                        "properties": {
                            "category": {"type": "string"},
                            "subject": {"type": "string"},
                            "pred_type": {"enum": ["binary", "enum", "numeric"]},
                            "value": {},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "stake_units": {"type": "number", "minimum": 0},
                            "odds": {}
                        }
                    }
                }
            }
        }

    def _get_default_registry(self) -> Dict[str, Any]:
        """Default category registry if file not found"""
        return {
            "game_winner": {
                "category": "game_winner",
                "pred_type": "enum",
                "subjects": [""],
                "constraints": {
                    "valid_values": ["home", "away"]
                }
            }
            # Add other categories as needed
        }


# Singleton instance
expert_predictions_validator = ExpertPredictionsValidator()
