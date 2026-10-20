import { term, plural } from './contract';

export const outcomeInfo = {
  understand: { title: 'UNDERSTAND', question: 'What is happening in my business right now?' },
  decide: { title: 'DECIDE', question: 'What should I do about it?' },
  monitor: { title: 'MONITOR', question: 'Is my business on track without me checking manually?' }
};
export const labels = () => ({
  revenue: term('revenue'), customer: term('customer'), customers: plural(term('customer')),
  product: term('product'), products: plural(term('product')), transaction: term('transaction')
});
