import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StudentTable from '../components/StudentTable.vue'

const students = [
  { id: 1, first_name: 'Олена', last_name: 'Коваль', average: 91.5 },
  { id: 5, first_name: 'Софія', last_name: 'Ткачук', average: null },
]

describe('StudentTable', () => {
  it('показує рядок для кожного студента з форматованим балом', () => {
    const wrapper = mount(StudentTable, { props: { students } })
    const rows = wrapper.findAll('tr').slice(1)
    expect(rows).toHaveLength(2)
    expect(rows[0].text()).toContain('Коваль Олена')
    expect(rows[0].text()).toContain('91,5')
    expect(rows[1].find('td.empty').text()).toBe('-')
  })

  it('повідомляє батьківський компонент про вибір', async () => {
    const wrapper = mount(StudentTable, { props: { students } })
    await wrapper.findAll('td button')[1].trigger('click')
    expect(wrapper.emitted('select')).toEqual([[students[1]]])
  })

  it('передає студента у слот actions', () => {
    const wrapper = mount(StudentTable, {
      props: { students },
      slots: {
        actions: ({ student }) => `Дія для ${student.last_name}`,
      },
    })
    const rows = wrapper.findAll('tr').slice(1)
    expect(rows[0].text()).toContain('Дія для Коваль')
    expect(rows[1].text()).toContain('Дія для Ткачук')
  })
})
