'use client';
import * as Dialog from '@radix-ui/react-dialog';
import { Button } from '../Shared/Button';

export default function SettingsModal() {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button>Settings</Button>
      </Dialog.Trigger>
      <Dialog.Content className="rounded-2xl bg-background p-4 shadow">
        <Dialog.Title className="text-lg font-bold">Settings & FAQ</Dialog.Title>
        <p className="mt-2 text-sm">Coming soon...</p>
        <Dialog.Close asChild>
          <Button className="mt-4">Close</Button>
        </Dialog.Close>
      </Dialog.Content>
    </Dialog.Root>
  );
}
