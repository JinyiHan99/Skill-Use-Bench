# Source and preparation

Source: https://raw.githubusercontent.com/lobehub/lobe-chat/main/src/features/SkillStore/index.tsx

Preparation:
- Kept the real SkillStore modal file content from the public LobeChat repository.
- Added a minimal provider composition file that reflects a common migration state: the app has the older global modal host mounted, while the newly migrated feature opens through the newer modal stack.
- Directory layout mirrors the original project paths needed by the task.
