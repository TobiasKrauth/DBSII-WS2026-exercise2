from dbs2.dbms import Relation, RelationSizeExceedsCapacityError
from dbs2.dbms.utils.block_sorter import sort_blocks

from .sort_operation import SortOperation


class TPMMS(SortOperation):
    def estimated_io_cost(self, input_relation: Relation) -> int:
        return 3 * input_relation.estimated_block_count()
        raise NotImplementedError("TODO")

    def sort(self, input_relation: Relation, output_relation: Relation) -> None:
        blockManager = self.block_manager
        freeBlocks = blockManager.free_blocks
        allBlocksCount = input_relation.estimated_block_count()
        key = input_relation.columns.get_column_key(self.sort_column_index)

        # Phase 1
        allIterations = (allBlocksCount + freeBlocks - 1) // freeBlocks
        if allIterations > freeBlocks - 1:
            raise RelationSizeExceedsCapacityError()

        references = iter(input_relation)
        runs = []

        for iteration in range(allIterations):
            remaining = allBlocksCount - iteration * freeBlocks
            sixToSeven = min(freeBlocks, remaining)

            fullyLoaded = []
            for _ in range(sixToSeven):
                fullyLoaded.append(blockManager.load(next(references)))

            sort_blocks(fullyLoaded, key)

            blockReference = []
            for block in fullyLoaded:
                blockReference.append(blockManager.write_to_disk(block))
                block.close()
            runs.append(blockReference)

        # Phase 2
        currentBlocks = []
        nexPositionsInBlock = []
        nextBlockIndex = []
        for run in runs:
            currentBlocks.append(blockManager.load(run[0]))
            nexPositionsInBlock.append(0)
            nextBlockIndex.append(1)

        outputBlock = blockManager.allocate(in_memory=True)

        while True:
            smallest = None
            for i in range(len(runs)):
                if currentBlocks[i] is None:
                    continue
                if smallest is None or key(currentBlocks[i][nexPositionsInBlock[i]]) < key(
                    currentBlocks[smallest][nexPositionsInBlock[smallest]]
                ):
                    smallest = i
            
            if smallest is None:
                break

            if outputBlock.is_full:
                output_relation.get_block_input().move(outputBlock)
                outputBlock = blockManager.allocate(in_memory=True)

            outputBlock.append(currentBlocks[smallest][nexPositionsInBlock[smallest]])
            nexPositionsInBlock[smallest] += 1

            if nexPositionsInBlock[smallest] == currentBlocks[smallest].size:
                currentBlocks[smallest].close()
                run = runs[smallest]
                if nextBlockIndex[smallest] < len(run):
                    currentBlocks[smallest] = blockManager.load(run[nextBlockIndex[smallest]])
                    nextBlockIndex[smallest] += 1
                    nexPositionsInBlock[smallest] = 0
                else:
                    currentBlocks[smallest] = None

        output_relation.get_block_input().move(outputBlock)
        return
        raise NotImplementedError("TODO")

