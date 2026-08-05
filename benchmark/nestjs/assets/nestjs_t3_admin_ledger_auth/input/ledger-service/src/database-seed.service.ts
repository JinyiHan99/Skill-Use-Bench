import { Injectable, OnModuleInit } from '@nestjs/common';
import { AccountsRepository } from './accounts/accounts.repository';
import { LedgerRepository } from './ledger/ledger.repository';
import { ProjectsRepository } from './projects/projects.repository';

@Injectable()
export class DatabaseSeedService implements OnModuleInit {
  constructor(
    private readonly accountsRepository: AccountsRepository,
    private readonly ledgerRepository: LedgerRepository,
    private readonly projectsRepository: ProjectsRepository,
  ) {}

  async onModuleInit(): Promise<void> {
    await this.accountsRepository.migrate();
    await this.ledgerRepository.migrate();
    await this.projectsRepository.migrate();
    await this.accountsRepository.seed();
    await this.projectsRepository.seed();
  }
}
