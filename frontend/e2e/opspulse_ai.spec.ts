import { test, expect } from '@playwright/test';

test.describe('OpsPulse AI — AI-Generated E2E Automated Test Suite', () => {

  test('TC-AUTH-06: User can log in with development seed credentials and access dashboard', async ({ page }) => {
    await page.goto('/login');

    // Verify login page loaded with expected elements
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();

    // Fill credentials
    await page.fill('[data-testid="input-login-email"]', 'admin@opspulse.local');
    await page.fill('[data-testid="input-login-password"]', 'admin123');

    // Submit form
    await page.click('[data-testid="btn-login-submit"]');

    // Wait for redirect to dashboard
    await expect(page.locator('[data-testid="stat-active-incidents"]')).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Service Reliability Dashboard')).toBeVisible();
  });

  test('TC-DASH-04: Dashboard displays 6 metric KPI cards with live telemetry', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="input-login-email"]', 'admin@opspulse.local');
    await page.fill('[data-testid="input-login-password"]', 'admin123');
    await page.click('[data-testid="btn-login-submit"]');

    await expect(page.locator('[data-testid="stat-active-incidents"]')).toBeVisible();
    await expect(page.locator('[data-testid="stat-critical-incidents"]')).toBeVisible();
    await expect(page.locator('[data-testid="stat-unack-incidents"]')).toBeVisible();
    await expect(page.locator('[data-testid="stat-resolved-incidents"]')).toBeVisible();
    await expect(page.locator('[data-testid="stat-total-services"]')).toBeVisible();
    await expect(page.locator('[data-testid="stat-failing-services"]')).toBeVisible();
  });

  test('TC-SRVC-05: Services catalog renders registered microservices with health badges', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="input-login-email"]', 'admin@opspulse.local');
    await page.fill('[data-testid="input-login-password"]', 'admin123');
    await page.click('[data-testid="btn-login-submit"]');

    // Navigate to services
    await page.click('[data-testid="nav-services"]');
    await expect(page).toHaveURL('/services');
    await expect(page.locator('[data-testid="services-grid"]')).toBeVisible();

    // Verify at least one service card rendered
    const cards = page.locator('[data-testid^="service-card-"]');
    await expect(cards.first()).toBeVisible();
  });

  test('TC-ALRT-06: Simulate alert webhook from command bar and receive confirmation', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="input-login-email"]', 'admin@opspulse.local');
    await page.fill('[data-testid="input-login-password"]', 'admin123');
    await page.click('[data-testid="btn-login-submit"]');

    // Open Simulate Alert modal from TopBar
    await page.click('[data-testid="btn-simulate-alert"]');
    await expect(page.locator('[data-testid="input-alert-title"]')).toBeVisible();

    // Fill alert details
    await page.fill('[data-testid="input-alert-title"]', 'Playwright Synthetic Probe E2E Alert');
    await page.selectOption('[data-testid="input-alert-severity"]', 'HIGH');

    // Dispatch
    await page.click('[data-testid="btn-submit-simulate-alert"]');

    // Verify confirmation feedback
    await expect(page.locator('text=Incident #')).toBeVisible({ timeout: 5000 });
  });

  test('TC-INCD-08: Incidents list renders and navigating to detail shows command actions', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="input-login-email"]', 'admin@opspulse.local');
    await page.fill('[data-testid="input-login-password"]', 'admin123');
    await page.click('[data-testid="btn-login-submit"]');

    // Navigate to incidents
    await page.click('[data-testid="nav-incidents"]');
    await expect(page).toHaveURL('/incidents');
    await expect(page.locator('[data-testid="incidents-table"]')).toBeVisible();

    // Click first row to view detail
    const firstRow = page.locator('[data-testid^="incident-row-"]').first();
    await firstRow.click();

    // Verify detail page has action buttons
    await expect(page.locator('[data-testid="btn-action-assign"]')).toBeVisible();
  });

});
