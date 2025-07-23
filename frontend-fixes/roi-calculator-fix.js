// ROI Calculator Fix for Chime Website
// This script provides essential fixes for form submission issues

(function() {
    'use strict';
    
    console.log('🔧 Loading ROI Calculator fixes...');
    
    // Fix 1: Enhanced form submission handler
    function createFixedROICalculator() {
        function validateForm(formData) {
            const required = ['monthly_revenue'];
            const missing = required.filter(field => !formData[field] || formData[field] === '');
            
            if (missing.length > 0) {
                return { valid: false, error: `Missing required fields: ${missing.join(', ')}` };
            }
            
            if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
                return { valid: false, error: 'Invalid email format' };
            }
            
            return { valid: true };
        }
        
        function calculateROI(formData) {
            const monthlyRevenue = parseFloat(formData.monthly_revenue) || 0;
            const conversionRate = parseFloat(formData.conversion_rate) || 2.5;
            const cartAbandonment = parseFloat(formData.cart_abandonment) || 70;
            const adSpend = parseFloat(formData.monthly_ad_spend) || 5000;
            const manualHours = parseFloat(formData.manual_hours) || 35;
            
            const revenueIncrease = monthlyRevenue * 0.25;
            const timeSavings = manualHours * 0.8;
            const adEfficiency = adSpend * 0.15;
            
            const totalMonthlyGain = revenueIncrease + (timeSavings * 50) + adEfficiency;
            const annualGain = totalMonthlyGain * 12;
            
            return {
                monthly_gain: Math.round(totalMonthlyGain),
                annual_gain: Math.round(annualGain),
                time_saved: Math.round(timeSavings),
                efficiency_gain: Math.round(adEfficiency),
                roi_percentage: Math.round((annualGain / (adSpend * 12)) * 100)
            };
        }
        
        async function submitForm(formData) {
            try {
                const validation = validateForm(formData);
                if (!validation.valid) {
                    throw new Error(validation.error);
                }
                
                const roiResults = calculateROI(formData);
                
                const submitData = {
                    ...formData,
                    ...roiResults,
                    timestamp: new Date().toISOString(),
                    source: 'roi_calculator_fixed'
                };
                
                // Try multiple endpoints
                const endpoints = ['/api/roi-calculator', '/api/submit-roi', '/api/contact'];
                let lastError;
                
                for (const endpoint of endpoints) {
                    try {
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify(submitData)
                        });
                        
                        if (response.ok) {
                            const result = await response.json();
                            return {
                                success: true,
                                data: result,
                                calculations: roiResults
                            };
                        }
                    } catch (error) {
                        lastError = error;
                        continue;
                    }
                }
                
                // If all endpoints fail, still return calculations
                return {
                    success: false,
                    error: lastError?.message || 'Submission failed',
                    calculations: roiResults
                };
                
            } catch (error) {
                console.error('ROI Calculator error:', error);
                return {
                    success: false,
                    error: error.message,
                    calculations: calculateROI(formData)
                };
            }
        }
        
        return { validateForm, calculateROI, submitForm };
    }
    
    // Fix 2: Session management
    function fixSessionIssues() {
        try {
            // Clear HubSpot session conflicts
            const hubspotKeys = Object.keys(localStorage).filter(key => 
                key.includes('hubspot') || key.includes('hs-') || key.includes('_hs')
            );
            hubspotKeys.forEach(key => {
                try {
                    localStorage.removeItem(key);
                } catch (e) {
                    // Ignore errors
                }
            });
            
            // Check for redirect loops
            const currentUrl = window.location.href;
            if (currentUrl.includes('hubspot.com') && currentUrl.includes('sequences')) {
                window.location.href = 'https://www.chimehq.co/#/roi-calculator';
                return;
            }
            
            console.log('✅ Session issues fixed');
        } catch (error) {
            console.warn('Session fix warning:', error);
        }
    }
    
    // Fix 3: Enhanced form handling
    function enhanceFormHandling() {
        // Wait for DOM to be ready
        function waitForElement(selector, timeout = 10000) {
            return new Promise((resolve, reject) => {
                const element = document.querySelector(selector);
                if (element) {
                    resolve(element);
                    return;
                }
                
                const observer = new MutationObserver((mutations, obs) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        obs.disconnect();
                        resolve(element);
                    }
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                setTimeout(() => {
                    observer.disconnect();
                    reject(new Error(`Element ${selector} not found within ${timeout}ms`));
                }, timeout);
            });
        }
        
        // Enhance any existing forms
        function enhanceForms() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                // Add enhanced submit handler
                form.addEventListener('submit', async function(e) {
                    const action = form.action;
                    if (action && (action.includes('roi') || action.includes('calculator'))) {
                        e.preventDefault();
                        
                        const formData = new FormData(form);
                        const data = Object.fromEntries(formData.entries());
                        
                        const calculator = createFixedROICalculator();
                        const result = await calculator.submitForm(data);
                        
                        if (result.success) {
                            console.log('✅ Form submitted successfully:', result);
                            // Show success message or redirect
                            if (result.calculations) {
                                console.log('📊 ROI Calculations:', result.calculations);
                            }
                        } else {
                            console.error('❌ Form submission failed:', result.error);
                            // Still show calculations if available
                            if (result.calculations) {
                                console.log('📊 ROI Calculations (offline):', result.calculations);
                            }
                        }
                    }
                });
            });
        }
        
        // Run form enhancement
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', enhanceForms);
        } else {
            enhanceForms();
        }
        
        // Also watch for dynamically added forms
        const observer = new MutationObserver(enhanceForms);
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    // Initialize all fixes
    function initialize() {
        console.log('🚀 Initializing ROI Calculator fixes...');
        
        fixSessionIssues();
        enhanceFormHandling();
        
        // Expose calculator globally
        window.ChimeROICalculator = createFixedROICalculator();
        
        console.log('✅ ROI Calculator fixes loaded successfully');
    }
    
    // Run initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
})();

