/**
 * Accessibility utility functions for NFL Dashboard
 * Provides helper functions for ARIA labels, keyboard navigation, and screen reader support
 */

/**
 * Generate accessible labels for team matchups
 * @param {string} awayTeam - Away team abbreviation
 * @param {string} homeTeam - Home team abbreviation
 * @param {number} winProb - Win probability for home team
 * @returns {string} Accessible label for screen readers
 */
export const getGameAccessibilityLabel = (awayTeam, homeTeam, winProb) => {
  const homeProbability = Math.round(winProb * 100);
  const awayProbability = 100 - homeProbability;
  
  return `Game between ${awayTeam} and ${homeTeam}. ${homeTeam} has ${homeProbability}% win probability, ${awayTeam} has ${awayProbability}% win probability.`;
};

/**
 * Generate accessible labels for spread information
 * @param {string} team - Team abbreviation
 * @param {number} spread - Point spread
 * @param {number} modelSpread - Model's projected spread
 * @returns {string} Accessible label for screen readers
 */
export const getSpreadAccessibilityLabel = (team, spread, modelSpread) => {
  const spreadText = spread > 0 ? `${team} is ${spread} point underdog` : `${team} is ${Math.abs(spread)} point favorite`;
  const modelText = modelSpread > 0 ? `Model projects ${team} as ${modelSpread} point underdog` : `Model projects ${team} as ${Math.abs(modelSpread)} point favorite`;
  
  return `${spreadText}. ${modelText}.`;
};

/**
 * Generate accessible labels for expected value
 * @param {number} ev - Expected value as decimal
 * @param {number} confidence - Confidence level as decimal
 * @returns {string} Accessible label for screen readers
 */
export const getEVAccessibilityLabel = (ev, confidence) => {
  const evPercent = (ev * 100).toFixed(1);
  const confidencePercent = (confidence * 100).toFixed(0);
  const evDescription = ev > 0.1 ? 'high positive' : ev > 0.05 ? 'moderate positive' : ev > 0 ? 'low positive' : 'negative';
  
  return `Expected value: ${evPercent}%. This is a ${evDescription} expected value bet with ${confidencePercent}% confidence.`;
};

/**
 * Generate accessible labels for power rankings
 * @param {string} team - Team abbreviation
 * @param {number} rank - Current rank
 * @param {number} movement - Rank movement from previous week
 * @param {number} elo - ELO rating
 * @returns {string} Accessible label for screen readers
 */
export const getRankingAccessibilityLabel = (team, rank, movement, elo) => {
  const movementText = movement > 0 ? `up ${movement} positions` : 
                      movement < 0 ? `down ${Math.abs(movement)} positions` : 
                      'unchanged';
  
  return `${team} is ranked ${rank} with ELO rating ${elo}. Movement from last week: ${movementText}.`;
};

/**
 * Generate accessible labels for EPA statistics
 * @param {number} offensiveEPA - Offensive EPA
 * @param {number} defensiveEPA - Defensive EPA
 * @returns {string} Accessible label for screen readers
 */
export const getEPAAccessibilityLabel = (offensiveEPA, defensiveEPA) => {
  const offenseDescription = offensiveEPA > 0.2 ? 'excellent' : 
                            offensiveEPA > 0.1 ? 'good' : 
                            offensiveEPA > 0 ? 'average' : 'below average';
  
  const defenseDescription = defensiveEPA < -0.15 ? 'excellent' : 
                            defensiveEPA < -0.1 ? 'good' : 
                            defensiveEPA < 0 ? 'average' : 'below average';
  
  return `Offensive EPA: ${offensiveEPA.toFixed(2)}, rated as ${offenseDescription}. Defensive EPA: ${defensiveEPA.toFixed(2)}, rated as ${defenseDescription}.`;
};

/**
 * Generate keyboard navigation instructions
 * @param {string} componentType - Type of component (table, card, button, etc.)
 * @returns {string} Keyboard navigation instructions
 */
export const getKeyboardInstructions = (componentType) => {
  const instructions = {
    table: 'Use arrow keys to navigate between cells, Enter to select, Escape to exit.',
    card: 'Use Tab to navigate between cards, Enter to select, Space to expand details.',
    button: 'Press Enter or Space to activate button.',
    tabs: 'Use arrow keys to navigate between tabs, Enter to select tab.',
    form: 'Use Tab to navigate between form fields, Enter to submit.'
  };
  
  return instructions[componentType] || 'Use Tab to navigate, Enter to select.';
};

/**
 * Check if element is visible to screen readers
 * @param {HTMLElement} element - DOM element to check
 * @returns {boolean} Whether element is accessible
 */
export const isAccessible = (element) => {
  if (!element) return false;
  
  const style = window.getComputedStyle(element);
  const isHidden = style.display === 'none' || 
                   style.visibility === 'hidden' || 
                   style.opacity === '0' ||
                   element.hasAttribute('aria-hidden');
  
  return !isHidden;
};

/**
 * Generate color-blind friendly descriptions for data visualizations
 * @param {string} colorClass - CSS color class
 * @returns {string} Color-blind friendly description
 */
export const getColorDescription = (colorClass) => {
  const colorMap = {
    'text-green-400': 'positive value, shown in green',
    'text-red-400': 'negative value, shown in red',
    'text-blue-400': 'neutral value, shown in blue',
    'text-yellow-400': 'caution value, shown in yellow',
    'text-purple-400': 'special value, shown in purple'
  };
  
  return colorMap[colorClass] || 'data value';
};

/**
 * Generate ARIA live region announcements for dynamic content updates
 * @param {string} updateType - Type of update (data, navigation, error, etc.)
 * @param {string} message - Update message
 * @returns {object} ARIA live region configuration
 */
export const getLiveRegionConfig = (updateType, message) => {
  const configs = {
    data: {
      'aria-live': 'polite',
      'aria-atomic': 'true',
      message: `Data updated: ${message}`
    },
    navigation: {
      'aria-live': 'assertive',
      'aria-atomic': 'true',
      message: `Navigation: ${message}`
    },
    error: {
      'aria-live': 'assertive',
      'aria-atomic': 'true',
      role: 'alert',
      message: `Error: ${message}`
    },
    success: {
      'aria-live': 'polite',
      'aria-atomic': 'true',
      message: `Success: ${message}`
    }
  };
  
  return configs[updateType] || configs.data;
};

/**
 * Focus management utilities
 */
export const focusUtils = {
  /**
   * Trap focus within a container element
   * @param {HTMLElement} container - Container element
   */
  trapFocus: (container) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    container.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    });
    
    firstElement.focus();
  },

  /**
   * Restore focus to previous element
   * @param {HTMLElement} element - Element to focus
   */
  restoreFocus: (element) => {
    if (element && typeof element.focus === 'function') {
      element.focus();
    }
  }
};

/**
 * Screen reader utility functions
 */
export const screenReaderUtils = {
  /**
   * Announce message to screen readers
   * @param {string} message - Message to announce
   * @param {string} priority - Priority level (polite, assertive)
   */
  announce: (message, priority = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  },

  /**
   * Update page title for screen readers
   * @param {string} title - New page title
   */
  updatePageTitle: (title) => {
    document.title = title;
  }
};

export default {
  getGameAccessibilityLabel,
  getSpreadAccessibilityLabel,
  getEVAccessibilityLabel,
  getRankingAccessibilityLabel,
  getEPAAccessibilityLabel,
  getKeyboardInstructions,
  isAccessible,
  getColorDescription,
  getLiveRegionConfig,
  focusUtils,
  screenReaderUtils
};