import { vi } from 'vitest';
import { config } from '@vue/test-utils';

// 模拟Element Plus组件
config.global.stubs = {
  'el-button': true,
  'el-upload': true,
  'el-progress': true,
  'el-message': true,
  'el-table': true,
  'el-table-column': true,
  'el-tag': true,
  'el-icon': true,
};

// 模拟全局对象
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// 模拟IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
})); 