import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../src/App.vue'

describe('M0 smoke', () => {
  it('renders the placeholder', () => {
    const wrapper = mount(App)
    expect(wrapper.find('h1').text()).toBe('SeedFoundry')
  })
})
