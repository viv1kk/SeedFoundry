// Base components (NFR-6): button, chip, card, modal, tooltip.

import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, nextTick, ref } from 'vue'
import BaseButton from '../src/components/base/BaseButton.vue'
import BaseCard from '../src/components/base/BaseCard.vue'
import BaseChip from '../src/components/base/BaseChip.vue'
import BaseModal from '../src/components/base/BaseModal.vue'
import BaseTooltip from '../src/components/base/BaseTooltip.vue'

afterEach(() => {
  document.body.innerHTML = ''
})

function press(key: string, shiftKey = false): void {
  const target = document.activeElement ?? document.body
  target.dispatchEvent(new KeyboardEvent('keydown', { key, shiftKey, bubbles: true, cancelable: true }))
}

describe('BaseButton', () => {
  it('is a native button of type button, secondary by default', () => {
    const wrapper = mount(BaseButton, { slots: { default: 'Cancel' } })
    const button = wrapper.find('button')
    expect(button.attributes('type')).toBe('button')
    expect(button.classes()).toContain('button--secondary')
    expect(button.text()).toBe('Cancel')
  })

  it('has a primary variant', () => {
    const wrapper = mount(BaseButton, { props: { variant: 'primary' }, slots: { default: 'Approve' } })
    expect(wrapper.find('button').classes()).toContain('button--primary')
  })

  it('does not fire when disabled', async () => {
    let clicks = 0
    const wrapper = mount(BaseButton, { props: { disabled: true, onClick: () => clicks++ } })
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    expect(clicks).toBe(0)
  })
})

describe('BaseChip', () => {
  it.each(['neutral', 'accent', 'positive', 'warning', 'negative'] as const)('has a %s tone', (tone) => {
    const wrapper = mount(BaseChip, { props: { tone }, slots: { default: 'Passed' } })
    expect(wrapper.classes()).toContain(`chip--${tone}`)
    expect(wrapper.text()).toBe('Passed')
  })
})

describe('BaseCard', () => {
  it('shows a title as a heading and its content', () => {
    const wrapper = mount(BaseCard, { props: { title: 'Tests' }, slots: { default: '<p>body</p>' } })
    expect(wrapper.find('h2').text()).toBe('Tests')
    expect(wrapper.find('.card__body p').text()).toBe('body')
  })

  it('has no header without a title', () => {
    expect(mount(BaseCard).find('header').exists()).toBe(false)
  })
})

describe('BaseModal', () => {
  const Host = defineComponent({
    components: { BaseModal, BaseButton },
    setup() {
      const open = ref(false)
      return { open }
    },
    template: `
      <div>
        <button id="opener" @click="open = true">Open</button>
        <BaseModal :open="open" title="Rebuild Seed: observer feedback" @close="open = false">
          <input id="first-field" />
          <template #footer>
            <button id="cancel" @click="open = false">Cancel</button>
            <button id="confirm">Start Rebuild</button>
          </template>
        </BaseModal>
      </div>`,
  })

  async function openModal() {
    const wrapper = mount(Host, { attachTo: document.body })
    const opener = document.getElementById('opener') as HTMLButtonElement
    opener.focus()
    opener.click()
    await nextTick()
    await nextTick()
    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    return { wrapper, opener, dialog }
  }

  it('is a labelled modal dialog', async () => {
    const { dialog } = await openModal()
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    const label = document.getElementById(dialog.getAttribute('aria-labelledby') ?? '')
    expect(label?.textContent).toBe('Rebuild Seed: observer feedback')
  })

  it('moves focus into the dialog when it opens', async () => {
    const { dialog } = await openModal()
    expect(dialog.contains(document.activeElement)).toBe(true)
  })

  it('traps Tab: from the last control to the first, and Shift+Tab from the first to the last', async () => {
    const { dialog } = await openModal()
    const items = Array.from(dialog.querySelectorAll<HTMLElement>('button, input'))
    const first = items[0]
    const last = items[items.length - 1]
    expect(last.id).toBe('confirm')
    last.focus()
    press('Tab')
    expect(document.activeElement).toBe(first)
    press('Tab', true)
    expect(document.activeElement).toBe(last)
  })

  it('closes on Escape and returns focus to the opener', async () => {
    const { opener } = await openModal()
    press('Escape')
    await nextTick()
    await nextTick()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(opener)
  })

  it('returns focus to the opener when closed by a button', async () => {
    const { opener } = await openModal()
    ;(document.getElementById('cancel') as HTMLButtonElement).click()
    await nextTick()
    await nextTick()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(opener)
  })

  it('has a Close button that closes it', async () => {
    await openModal()
    ;(document.querySelector('button[aria-label="Close"]') as HTMLButtonElement).click()
    await nextTick()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('does not close on a backdrop click', async () => {
    await openModal()
    ;(document.querySelector('.backdrop') as HTMLElement).click()
    await nextTick()
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
  })
})

describe('BaseTooltip', () => {
  function mountTooltip() {
    return mount(BaseTooltip, {
      props: { text: 'Voice input' },
      slots: { default: '<button type="button">mic</button>' },
      attachTo: document.body,
    })
  }

  it('describes its control', () => {
    const wrapper = mountTooltip()
    const tip = wrapper.find('[role="tooltip"]')
    expect(tip.text()).toBe('Voice input')
    expect(wrapper.find('button').attributes('aria-describedby')).toBe(tip.attributes('id'))
  })

  it('shows on keyboard focus and hides on blur', async () => {
    const wrapper = mountTooltip()
    const tip = () => wrapper.find('[role="tooltip"]')
    expect(tip().classes()).not.toContain('tooltip--visible')
    await wrapper.find('button').trigger('focusin')
    expect(tip().classes()).toContain('tooltip--visible')
    await wrapper.find('button').trigger('focusout')
    expect(tip().classes()).not.toContain('tooltip--visible')
  })

  it('shows on hover and hides on Escape', async () => {
    const wrapper = mountTooltip()
    await wrapper.trigger('mouseenter')
    expect(wrapper.find('[role="tooltip"]').classes()).toContain('tooltip--visible')
    await wrapper.find('button').trigger('keydown', { key: 'Escape' })
    expect(wrapper.find('[role="tooltip"]').classes()).not.toContain('tooltip--visible')
  })
})
