import { act, create, type ReactTestRenderer } from "react-test-renderer";
import { MemoryRouter, useLocation } from "react-router-dom";

export async function mountHook<T>(hook: () => T) {
  let current: T;
  let path: string;
  let renderer: ReactTestRenderer;
  function Probe() {
    current = hook();
    path = useLocation().pathname;
    return null;
  }
  await act(async () => {
    renderer = create(
      <MemoryRouter>
        <Probe />
      </MemoryRouter>,
    );
  });
  return {
    value: () => current!,
    path: () => path!,
    unmount: () => act(() => renderer!.unmount()),
  };
}
