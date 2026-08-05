# BlockingCollection<T>.GetConsumingEnumerable Method

Provides a consuming IEnumerable<T> for items in the collection.

The following example shows how to use the GetConsumingEnumerable method. It demonstrates BlockingCollection<T>.Add(), BlockingCollection<T>.CompleteAdding(), and BlockingCollection<T>.GetConsumingEnumerable().

The enumerator will continue to provide items, if any exist, until IsCompleted returns true. If IsCompleted is false, the loop blocks until an item becomes available or until the CancellationToken is cancelled.

This method enables client code to remove items from the collection by using a foreach loop, Parallel.ForEach, or a PLINQ query.
