import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import FileUploader from '@/components/FileUploader.vue';

describe('FileUploader', () => {
  it('renders properly', () => {
    const wrapper = mount(FileUploader, {
      props: {
        accept: '.pdf,.png,.jpg',
        maxSize: 50 * 1024 * 1024, // 50MB
      },
    });
    expect(wrapper.text()).toContain('拖拽文件到此处');
  });

  it('validates file type', async () => {
    const wrapper = mount(FileUploader, {
      props: {
        accept: '.pdf',
        maxSize: 50 * 1024 * 1024,
      },
    });

    // 模拟文件上传
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const input = wrapper.find('input[type="file"]');
    
    // 触发文件选择事件
    Object.defineProperty(input.element, 'files', {
      value: [file],
      writable: false,
    });
    
    await input.trigger('change');
    
    // 验证错误提示
    expect(wrapper.text()).toContain('文件类型不支持');
  });

  it('validates file size', async () => {
    const wrapper = mount(FileUploader, {
      props: {
        accept: '.pdf',
        maxSize: 1024, // 1KB
      },
    });

    // 创建大文件
    const largeFile = new File(['x'.repeat(2048)], 'large.pdf', {
      type: 'application/pdf',
    });
    
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [largeFile],
      writable: false,
    });
    
    await input.trigger('change');
    
    // 验证错误提示
    expect(wrapper.text()).toContain('文件大小超出限制');
  });
}); 