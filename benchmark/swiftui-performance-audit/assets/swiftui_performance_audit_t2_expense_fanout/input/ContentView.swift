//
//  ContentView.swift
//  iExpense
//
//  Created by Paul Hudson on 15/10/2023.
//

import SwiftUI

struct ExpenseItem: Identifiable, Codable, Equatable {
    let id: UUID
    let name: String
    let type: String
    let amount: Double

    init(id: UUID = UUID(), name: String, type: String, amount: Double) {
        self.id = id
        self.name = name
        self.type = type
        self.amount = amount
    }
}

@Observable
class Expenses {
    var items = [ExpenseItem]() {
        didSet {
            saveItems()
        }
    }

    init() {
        if let savedItems = UserDefaults.standard.data(forKey: "Items") {
            if let decodedItems = try? JSONDecoder().decode([ExpenseItem].self, from: savedItems) {
                items = decodedItems
                return
            }
        }

        items = []
    }

    private var saveTask: Task<Void, Never>?

    /// Debounced persistence: coalesces rapid mutations into a single encode + write,
    /// and runs the work off the main thread.
    private func saveItems() {
        saveTask?.cancel()
        saveTask = Task.detached(priority: .utility) { [items] in
            try? await Task.sleep(for: .milliseconds(200))
            guard !Task.isCancelled else { return }
            if let encoded = try? JSONEncoder().encode(items) {
                UserDefaults.standard.set(encoded, forKey: "Items")
            }
        }
    }
}

/// Extracted row view with Equatable conformance so SwiftUI can skip
/// body re-evaluation for unchanged rows when the list mutates.
struct ExpenseRowView: View, Equatable {
    let item: ExpenseItem

    static func == (lhs: ExpenseRowView, rhs: ExpenseRowView) -> Bool {
        lhs.item == rhs.item
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading) {
                Text(item.name)
                    .font(.headline)
                Text(item.type)
            }
            Spacer()
            Text(item.amount, format: .currency(code: "USD"))
        }
    }
}

struct ContentView: View {
    @State private var expenses = Expenses()
    @State private var showingAddExpense = false

    var body: some View {
        NavigationStack {
            List {
                ForEach(expenses.items) { item in
                    ExpenseRowView(item: item)
                }
                .onDelete(perform: removeItems)
            }
            .navigationTitle("iExpense")
            .toolbar {
                Button("Add Expense", systemImage: "plus") {
                    showingAddExpense = true
                }
            }
            .sheet(isPresented: $showingAddExpense) {
                AddView(expenses: expenses)
            }
        }
    }

    func removeItems(at offsets: IndexSet) {
        expenses.items.remove(atOffsets: offsets)
    }
}

#Preview {
    ContentView()
}
