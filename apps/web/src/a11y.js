// 클릭 가능한 행을 키보드로도 조작 가능하게(WCAG 2.1.1, 가이드 §8.1).
// div onClick 패턴에 스프레드로 적용: <div {...rowButtonProps(open)}>
export const rowButtonProps = (onActivate) => ({
  role: 'button',
  tabIndex: 0,
  onClick: onActivate,
  onKeyDown: (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onActivate(e)
    }
  },
})
