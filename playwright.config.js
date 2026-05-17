// playwright.config.js — SQM v8.6.8 회귀 테스트 설정
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 15000,
  use: {
    baseURL: 'http://127.0.0.1:8765',
    headless: false,
  },
  reporter: 'list',
});
