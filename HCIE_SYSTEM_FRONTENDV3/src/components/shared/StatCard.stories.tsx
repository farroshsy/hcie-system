import type { Meta, StoryObj } from '@storybook/react'
import { StatCard } from './stat_card'

const meta: Meta<typeof StatCard> = {
  title: 'Shared/StatCard',
  component: StatCard,
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    value: { control: 'text' },
    change: { control: 'number' },
    changeLabel: { control: 'text' },
    variant: { control: 'select', options: ['default', 'success', 'warning', 'error'] },
    loading: { control: 'boolean' },
  },
}

export default meta
type Story = StoryObj<typeof StatCard>

export const Default: Story = {
  args: {
    title: 'Tasks Completed',
    value: 38,
    change: 12,
    changeLabel: 'vs last period',
  },
}

export const Negative: Story = {
  args: {
    title: 'Errors',
    value: 3,
    change: -2,
    changeLabel: 'vs last period',
    variant: 'error',
  },
}

export const Success: Story = {
  args: {
    title: 'Average Score',
    value: '85%',
    change: 5,
    changeLabel: 'vs last period',
    variant: 'success',
  },
}

export const Loading: Story = {
  args: {
    title: 'Loading...',
    value: 0,
    loading: true,
  },
}
